// Execute the exact script produced by the simulator's shared native request
// builder against a fake debugserver. Nothing attaches to a device here.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const sample = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const template = fs.readFileSync(process.argv[3], 'utf8');
const oldLength = Number(process.argv[4]);
assert.equal(sample.request.length, 33554432);
assert.equal(sample.request.protocol, 1);
assert.equal(sample.request.pageSize, 16384);
assert.ok(sample.session_script.endsWith(template));
assert.equal(sample.compiled_protocol.bytes_per_arena, sample.request.length);
const initial = Buffer.from(sample.mailbox_hex, 'hex');
assert.equal(initial.length, 96);
assert.equal(initial.subarray(0, 48).toString('hex'), sample.request.header);
assert.equal(Number(initial.readBigUInt64LE(40)), sample.request.length);
assert.equal(Number(initial.readBigUInt64LE(32)), sample.request.pid);
function run(script, bytes, pid = sample.request.pid) {
    const mailbox = Buffer.from(bytes), base = BigInt(sample.request.mailbox);
    const commands = [], pageWrites = [], logs = [];
    let allocations = 0, error;
    const context = {get_pid: () => pid, log: text => logs.push(text), send_command: command => {
        commands.push(command);
        if (command.startsWith('vAttach;')) return 'T13thread:1;';
        if (command === 'D') return 'OK';
        if (command.startsWith('_M')) {
            assert.equal(command, '_M2000000,rx');
            return (0x120000000n + BigInt(++allocations) * 33554432n).toString(16);
        }
        if (command.startsWith('m')) {
            const [, address, length] = /^m([0-9a-f]+),([0-9a-f]+)$/.exec(command);
            const offset = Number(BigInt('0x' + address) - base), count = parseInt(length, 16);
            assert.ok(offset >= 0 && offset + count <= mailbox.length);
            return mailbox.subarray(offset, offset + count).toString('hex');
        }
        if (command.startsWith('M')) {
            const [, address, length, hex] = /^M([0-9a-f]+),([0-9a-f]+):([0-9a-f]+)$/.exec(command);
            assert.equal(parseInt(length, 16), hex.length / 2);
            const pointer = BigInt('0x' + address), offset = Number(pointer - base);
            if (offset >= 0 && offset < 96) {
                assert.ok(offset + hex.length / 2 <= 96);
                Buffer.from(hex, 'hex').copy(mailbox, offset);
            } else { assert.equal(hex, '69'); pageWrites.push(pointer); }
            return 'OK';
        }
        throw new Error('Unexpected debugserver command');
    }};
    try { vm.runInNewContext(script, context, {timeout: 1000}); } catch (caught) { error = caught; }
    return {mailbox, commands, allocations, pageWrites, logs, error};
}
const fixed = run(sample.session_script, initial);
assert.equal(fixed.error, undefined);
assert.equal(fixed.allocations, 2);
assert.equal(fixed.pageWrites.length, 4096);
assert.equal(new Set(fixed.pageWrites).size, 4096);
assert.equal(fixed.mailbox.readBigUInt64LE(48), 2n);
assert.equal(fixed.mailbox.readBigUInt64LE(72), 33554432n);
assert.equal(fixed.commands.at(-1), 'D');

// Recreate the observed build-7 request using the length obtained by compiling
// its preserved source with its recorded include flags. The script must reject
// it before issuing any attach or write command, exactly as on the phone.
assert.equal(oldLength, 65536);
const oldMailbox = Buffer.from(initial); oldMailbox.writeBigUInt64LE(BigInt(oldLength), 40);
const oldRequest = {...sample.request, length: oldLength, header: oldMailbox.subarray(0, 48).toString('hex')};
const old = run('const CJIT_REQUEST = ' + JSON.stringify(oldRequest) + ';\n' + template, oldMailbox);
assert.match(String(old.error), /Unsupported request geometry\/version/);
assert.equal(old.commands.length, 0);
const previousMailbox = Buffer.from(initial); previousMailbox.writeBigUInt64LE(4194304n, 40);
const previousRequest = {...sample.request, length: 4194304, header: previousMailbox.subarray(0, 48).toString('hex')};
const previous = run('const CJIT_REQUEST = ' + JSON.stringify(previousRequest) + ';\n' + template, previousMailbox);
assert.match(String(previous.error), /Unsupported request geometry\/version/);
assert.equal(previous.commands.length, 0);
const build12Mailbox = Buffer.from(initial); build12Mailbox.writeBigUInt64LE(16777216n, 40);
const build12Request = {...sample.request, length: 16777216, header: build12Mailbox.subarray(0, 48).toString('hex')};
const build12 = run('const CJIT_REQUEST = ' + JSON.stringify(build12Request) + ';\n' + template, build12Mailbox);
assert.match(String(build12.error), /Unsupported request geometry\/version/);
assert.equal(build12.commands.length, 0);
const stale = Buffer.from(initial); stale[16] ^= 1;
const staleResult = run(sample.session_script, stale);
assert.ok(staleResult.error); assert.equal(staleResult.allocations, 0);
assert.ok(!staleResult.commands.some(c => c.startsWith('M')));
assert.equal(staleResult.commands.at(-1), 'D');
const wrongPID = run(sample.session_script, initial, sample.request.pid + 1);
assert.ok(wrongPID.error); assert.equal(wrongPID.commands.length, 0);
console.log(JSON.stringify({status: 'PASS_NATIVE_GENERATED_REQUEST_WITH_PACKAGED_SCRIPT',
    bytes_per_arena: 33554432, mailbox_bytes: 96, regions: 2, acknowledged_page_writes: 4096,
    request_response_and_detach: true, historical_build7_geometry_reproduced_and_rejected: true,
    previous_build8_budget_rejected: true, previous_build12_budget_rejected: true,
    stale_nonce_and_wrong_pid_rejected: true, real_debugger_commands_sent: 0, device_execution: false}));
