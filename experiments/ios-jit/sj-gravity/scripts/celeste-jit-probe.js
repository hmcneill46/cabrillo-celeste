// Celeste JIT managed canary, mailbox protocol 1.
// This is an unbound template. The running app prepends CJIT_REQUEST and supplies
// it through script-data, or exports a launch-specific .js for manual import.
// Protocol reference: https://github.com/stikdebug/StikJIT/blob/3623e725876f76aecb0520582ad6194bacb15d39/INTEGRATION.md
// Independent implementation; no debugger library is embedded in the app.
(function () {
    "use strict";
    let attached = false, matched = false, mailbox = 0n, phase = 1;
    const say = text => log("[CJIT-M1] " + text);
    const require = (condition, message) => { if (!condition) throw new Error(message); };
    const command = text => {
        const reply = send_command(text);
        require(typeof reply === "string" && reply.length > 0, "Empty reply to " + text.split(",")[0]);
        return reply;
    };
    const le64 = value => {
        let result = "", n = BigInt(value);
        require(n >= 0n && n < (1n << 64n), "Invalid uint64");
        for (let i = 0; i < 8; i++) { result += Number(n & 255n).toString(16).padStart(2, "0"); n >>= 8n; }
        return result;
    };
    const read = (address, length) => {
        const reply = command("m" + address.toString(16) + "," + length.toString(16));
        require(new RegExp("^[0-9a-fA-F]{" + (length * 2) + "}$").test(reply), "Memory read failed or was short");
        return reply.toLowerCase();
    };
    const write = (address, bytes) => {
        require(command("M" + address.toString(16) + "," + (bytes.length / 2).toString(16) + ":" + bytes) === "OK", "Memory write rejected");
    };
    const detach = () => {
        require(command("D") === "OK", "Detach not acknowledged; stop this StikDebug session before retrying");
        attached = false;
    };
    try {
        require(typeof CJIT_REQUEST === "object", "Unbound template. Use Enable with StikDebug or Export session script in the running probe.");
        const request = CJIT_REQUEST;
        require(request.protocol === 1 && request.pageSize === 16384 && request.length === 134217728, "Unsupported request geometry/version");
        require(Number.isSafeInteger(request.pid) && request.pid > 0 && get_pid() === request.pid, "Wrong or expired process. Regenerate the script in the running probe.");
        require(/^0x[0-9a-f]{1,12}$/.test(request.mailbox), "Invalid mailbox address");
        require(/^[0-9a-f]{96}$/.test(request.header), "Invalid request identity");
        mailbox = BigInt(request.mailbox);
        require(mailbox > 0n && mailbox % 16n === 0n, "Unaligned mailbox");
        say("Preparing two 128 MiB regions for PID " + request.pid + "; request " + request.requestID);
        phase = 2;
        const stop = command("vAttach;" + request.pid.toString(16));
        require(/^[TS][0-9a-fA-F]{2}/.test(stop), "Attach failed: " + stop);
        attached = true;
        phase = 3;
        const initial = read(mailbox, 96);
        require(initial.slice(0, 96) === request.header, "Mailbox identity mismatch: expired launch or incorrect target");
        require(initial.slice(96, 112) === le64(1), "Request is not waiting; never reuse a completed script");
        require(initial.slice(112) === "0".repeat(80), "Response was already modified; relaunch the probe");
        matched = true;
        const allocate = index => {
            phase = 10 + index;
            const reply = command("_M" + request.length.toString(16) + ",rx");
            require(/^[0-9a-fA-F]{1,12}$/.test(reply), "RX allocation failed: " + reply);
            const address = BigInt("0x" + reply);
            require(address > 0n && address % BigInt(request.pageSize) === 0n && address + BigInt(request.length) < (1n << 48n), "RX allocation returned invalid bounds");
            require(address + BigInt(request.length) <= mailbox || address >= mailbox + 96n, "RX allocation overlaps mailbox");
            phase = 20 + index;
            // Check EVERY debugserver page-write acknowledgement. The upstream
            // batch helper does not expose individual remote error replies.
            for (let offset = 0; offset < request.length; offset += request.pageSize) {
                write(address + BigInt(offset), "69");
            }
            say("Region " + index + " prepared at 0x" + address.toString(16) + ", " + request.length + " bytes");
            return address;
        };
        const first = allocate(1), second = allocate(2);
        const length = BigInt(request.length);
        require(first + length <= second || second + length <= first, "RX allocations overlap");
        phase = 30;
        const response = le64(first) + le64(second) + le64(length) + le64(1) + le64(0);
        write(mailbox + 56n, response);
        require(read(mailbox + 56n, 40) === response, "Response read-back mismatch");
        write(mailbox + 48n, le64(2));
        require(read(mailbox + 48n, 8) === le64(2), "Completion read-back mismatch");
        phase = 40;
        detach();
        say("PREPARED + DETACHED. Switch back to the existing probe. Only its execution tests can report PASS.");
    } catch (error) {
        say("FAIL phase " + phase + ": " + String(error.message || error));
        if (attached && matched) {
            try {
                write(mailbox + 88n, le64(phase));
                write(mailbox + 48n, le64(3));
            } catch (secondary) { say("Could not report failure to app: " + String(secondary)); }
        }
        if (attached) {
            try { detach(); } catch (secondary) { say("DETACH FAILED: " + String(secondary)); }
        }
        // A failed/uncertain transaction requires a fresh app process. Any RX
        // allocations from a partial failure die with that process.
        throw error;
    }
}());
