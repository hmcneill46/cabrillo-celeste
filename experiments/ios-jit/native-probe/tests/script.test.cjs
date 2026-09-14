// Host protocol tests: fake debugserver, never a claim about iOS JIT execution.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../scripts/celeste-jit-probe.js'), 'utf8');
const write64 = (buffer, offset, value) => buffer.writeBigUInt64LE(BigInt(value), offset);
function run(options = {}) {
    const mailbox = Buffer.alloc(96), base = 0x100001000n;
    mailbox.write('CJT0MBX1'); write64(mailbox, 8, 1);
    Buffer.from('1112131415161718191a1b1c1d1e1f20', 'hex').copy(mailbox, 16);
    write64(mailbox, 32, 501); write64(mailbox, 40, 65536); write64(mailbox, 48, 1);
    const request = {protocol: 1, pid: 501, mailbox: '0x' + base.toString(16),
        header: mailbox.subarray(0, 48).toString('hex'), length: 65536, pageSize: 16384, requestID: 'host-test'};
    if (options.mutateMailbox) options.mutateMailbox(mailbox);
    if (options.mutateRequest) options.mutateRequest(request);
    const commands = [], logs = [], pageWrites = [];
    let allocation = 0, error;
    const context = {get_pid: () => options.pid || 501, log: message => logs.push(message),
        send_command: command => {
            commands.push(command);
            if (options.reply) {
                const reply = options.reply(command, commands);
                if (reply !== undefined) return reply;
            }
            if (command.startsWith('vAttach;')) return 'T13thread:1;';
            if (command === 'D') return 'OK';
            if (command.startsWith('_M')) {
                assert.equal(command, '_M10000,rx');
                allocation++;
                return (0x120000000n + BigInt(allocation) * 0x10000n).toString(16);
            }
            if (command.startsWith('m')) {
                const [, address, length] = /^m([0-9a-f]+),([0-9a-f]+)$/.exec(command);
                const offset = Number(BigInt('0x' + address) - base), count = parseInt(length, 16);
                assert.ok(offset >= 0 && offset + count <= mailbox.length);
                return mailbox.subarray(offset, offset + count).toString('hex');
            }
            if (command.startsWith('M')) {
                const [, address, length, bytes] = /^M([0-9a-f]+),([0-9a-f]+):([0-9a-f]+)$/.exec(command);
                assert.equal(parseInt(length, 16), bytes.length / 2);
                const target = BigInt('0x' + address), offset = Number(target - base);
                if (offset >= 0 && offset < 96) Buffer.from(bytes, 'hex').copy(mailbox, offset);
                else { assert.equal(bytes, '69'); pageWrites.push(target); }
                return 'OK';
            }
            throw new Error('Unexpected remote command: ' + command);
        }};
    if (!options.unbound) context.CJIT_REQUEST = request;
    try { vm.runInNewContext(source, context, {timeout: 1000}); } catch (caught) { error = caught; }
    return {mailbox, commands, logs, pageWrites, allocation, error};
}
let count = 0;
function test(name, check) { check(); count++; process.stdout.write('PASS ' + name + '\n'); }
test('prepared arenas, full-width pointers, every page acknowledged, detach last', () => {
    const result = run(); assert.equal(result.error, undefined);
    assert.equal(result.mailbox.readBigUInt64LE(48), 2n);
    assert.equal(result.mailbox.readBigUInt64LE(56), 0x120010000n);
    assert.equal(result.mailbox.readBigUInt64LE(64), 0x120020000n);
    assert.equal(result.pageWrites.length, 8); assert.equal(new Set(result.pageWrites).size, 8);
    assert.equal(result.commands.at(-1), 'D');
});
test('unbound template never attaches', () => { const r = run({unbound: true}); assert.ok(r.error); assert.equal(r.commands.length, 0); });
test('wrong target PID never attaches', () => { const r = run({pid: 502}); assert.ok(r.error); assert.equal(r.commands.length, 0); });
test('unsupported geometry never attaches', () => { const r = run({mutateRequest: r => r.pageSize = 4096}); assert.ok(r.error); assert.equal(r.commands.length, 0); });
test('stale nonce detaches without memory writes', () => {
    const r = run({mutateMailbox: m => m[16] ^= 1}); assert.ok(r.error); assert.equal(r.allocation, 0);
    assert.ok(!r.commands.some(c => c.startsWith('M'))); assert.equal(r.commands.at(-1), 'D');
});
test('completed request cannot be reused', () => {
    const r = run({mutateMailbox: m => write64(m, 48, 2)}); assert.ok(r.error); assert.equal(r.allocation, 0);
    assert.equal(r.mailbox.readBigUInt64LE(48), 2n); assert.equal(r.commands.at(-1), 'D');
});
test('attach failure never reads or writes the target', () => {
    const r = run({reply: c => c.startsWith('vAttach') ? 'E01' : undefined}); assert.ok(r.error); assert.equal(r.commands.length, 1);
});
test('short identity read detaches without writes', () => {
    const r = run({reply: c => c.startsWith('m') ? '00' : undefined}); assert.ok(r.error);
    assert.ok(!r.commands.some(c => c.startsWith('M'))); assert.equal(r.commands.at(-1), 'D');
});
test('RX allocation rejection reports failure and detaches', () => {
    const r = run({reply: c => c.startsWith('_M') ? 'E01' : undefined}); assert.ok(r.error);
    assert.equal(r.mailbox.readBigUInt64LE(48), 3n); assert.equal(r.mailbox.readBigUInt64LE(88), 11n);
    assert.equal(r.commands.at(-1), 'D');
});
test('failed page write never publishes success', () => {
    const r = run({reply: c => c.endsWith(',1:69') ? 'E03' : undefined}); assert.ok(r.error);
    assert.equal(r.mailbox.readBigUInt64LE(48), 3n); assert.equal(r.mailbox.readBigUInt64LE(88), 21n);
    assert.equal(r.commands.at(-1), 'D');
});
test('overlapping arenas rejected', () => {
    const r = run({reply: c => c.startsWith('_M') ? '120010000' : undefined}); assert.ok(r.error);
    assert.equal(r.mailbox.readBigUInt64LE(48), 3n);
});
test('unaligned RX allocation rejected', () => {
    const r = run({reply: c => c.startsWith('_M') ? '120010001' : undefined}); assert.ok(r.error); assert.equal(r.pageWrites.length, 0);
});
test('response write rejection cannot become ready', () => {
    const r = run({reply: c => c.startsWith('M100001038,28:') ? 'E03' : undefined}); assert.ok(r.error);
    assert.equal(r.mailbox.readBigUInt64LE(48), 3n); assert.equal(r.mailbox.readBigUInt64LE(88), 30n);
});
test('read-back corruption cannot become ready', () => {
    const r = run({reply: c => c === 'm100001038,28' ? '0'.repeat(80) : undefined}); assert.ok(r.error);
    assert.equal(r.mailbox.readBigUInt64LE(48), 3n);
});
test('detach failure is explicit and revokes ready state', () => {
    const r = run({reply: c => c === 'D' ? 'E01' : undefined}); assert.ok(r.error);
    assert.equal(r.mailbox.readBigUInt64LE(48), 3n); assert.ok(r.logs.some(s => s.includes('DETACH FAILED')));
});
process.stdout.write(JSON.stringify({host_mock_tests_passed: count, device_execution: 'NOT TESTED'}) + '\n');
