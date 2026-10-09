# `/dev/pup_update0` → mailbox → SAMU research model

## Scope

This is a testable model, not a claim that the entire internal protocol is known.

```text
Userland decryptor
      |
      | open/ioctl + bounded descriptors
      v
/dev/pup_update0
      |
      v
Kernel PUP manager / verification logic
      |
      | secure request / shared buffer descriptor (hypothesis)
      v
Secure mailbox boundary
      |
      v
SAMU / secure processor / key slot
      |
      v
status, authenticated metadata or decrypted output buffer
```

## Confirmed interface evidence

The reviewed public decryptor at commit `9e1a75fe00e0c44576af01a595af5a31130188c9` uses `/dev/pup_update0` and the following published request values:

- `0xC0184401` — header operation described by the source as decrypt header;
- `0xC0184402` and `0xC0184403` — segment verification operations;
- `0xC0184404` — segment decryption operation;
- `0xC0284405` — block-oriented segment decryption operation.

These values are source-derived; their deeper kernel/mailbox mapping remains unverified.

## Questions for every edge

For each transition, determine:

1. caller and callee;
2. descriptor and buffer structure;
3. memory owner and address space;
4. allocation, mapping and lifetime;
5. validation before and after the trust boundary;
6. error propagation;
7. whether plaintext is returned in place, copied or consumed internally;
8. whether a key is raw, derived, slot-referenced or never x86-visible.

## Success levels

1. **Decrypt oracle:** protected input can be transformed into valid plaintext.
2. **Observable plaintext:** metadata and output buffers can be mapped and correlated.
3. **Protocol reconstruction:** kernel-to-secure-processor messages are understood.
4. **Temporary material observation:** derived transient material is demonstrated outside the secure boundary.
5. **Reusable key extraction:** a key reusable independently of the console operation is demonstrated.

Only the first level is presently supported as plausible by public decryptor designs. Levels 3–5 remain unverified.

## Static-first investigation order

1. Obtain legally sourced firmware versions 9.00, 9.03 and 13.52.
2. Identify the kernel-side PUP device implementation and request dispatch.
3. Recover request structures and state transitions from code, not guesses.
4. Identify memory mappings and secure-service call sites.
5. Build a bounded observation plan on the owner-controlled 9.00 console.
6. Compare ciphertext, returned data, errors and buffer lifetimes.
7. Escalate to passive hardware observation only for a named signal and unresolved question.

## Non-equivalence rules

```text
PUP plaintext recovery != PUP key export
PUP symmetric key      != Sony private signing key
kernel execution       != SAMU internal memory access
valid OpenOrbis PKG    != Sony retail authorization
custom PUP structure   != retail secure-boot acceptance
```
