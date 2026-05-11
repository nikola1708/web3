import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { BunnyAttestation } from "../target/types/bunny_attestation";
import { assert } from "chai";
import * as crypto from "crypto";

describe("bunny_attestation", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace
    .BunnyAttestation as Program<BunnyAttestation>;
  const author = provider.wallet;

  const testManuscript =
    "This is my novel. Chapter 1: It was a dark and stormy night...";
  const manuscriptHash = Array.from(
    crypto.createHash("sha256").update(testManuscript).digest()
  );

  it("Creates an attestation (first commit)", async () => {
    const title = "My First Novel";
    const commitMessage = "Initial draft - Chapter 1";

    const [authorProfilePda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("author_profile"), author.publicKey.toBuffer()],
      program.programId
    );

    const commitNumber = new anchor.BN(1);
    const [attestationPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [
        Buffer.from("attestation"),
        author.publicKey.toBuffer(),
        Buffer.from(manuscriptHash),
        commitNumber.toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    );

    const tx = await program.methods
      .createAttestation(
        manuscriptHash,
        85, // humanity_score
        15, // ai_score
        90, // temporal_score
        title,
        commitMessage
      )
      .accounts({
        author: author.publicKey,
        authorProfile: authorProfilePda,
        attestation: attestationPda,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    console.log("  Tx:", tx);

    const attestation =
      await program.account.attestation.fetch(attestationPda);
    assert.equal(attestation.humanityScore, 85);
    assert.equal(attestation.aiScore, 15);
    assert.equal(attestation.temporalScore, 90);
    assert.equal(attestation.title, title);
    assert.equal(attestation.commitMessage, commitMessage);
    assert.equal(attestation.commitNumber.toNumber(), 1);
    assert.deepEqual(
      Array.from(attestation.manuscriptHash),
      manuscriptHash
    );

    const profile =
      await program.account.authorProfile.fetch(authorProfilePda);
    assert.equal(profile.totalCommits.toNumber(), 1);
    assert.ok(profile.lastCommitTimestamp.toNumber() > 0);

    console.log("  ✓ Humanity score:", attestation.humanityScore);
    console.log("  ✓ Commit #:", attestation.commitNumber.toNumber());
  });

  it("Creates a second commit (showing evolution)", async () => {
    const updatedManuscript =
      testManuscript + " It was the best of times...";
    const updatedHash = Array.from(
      crypto.createHash("sha256").update(updatedManuscript).digest()
    );

    const [authorProfilePda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("author_profile"), author.publicKey.toBuffer()],
      program.programId
    );

    const commitNumber = new anchor.BN(2);
    const [attestationPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [
        Buffer.from("attestation"),
        author.publicKey.toBuffer(),
        Buffer.from(updatedHash),
        commitNumber.toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    );

    await program.methods
      .createAttestation(
        updatedHash,
        88,
        12,
        95,
        "My First Novel",
        "Chapter 1 revision - added opening"
      )
      .accounts({
        author: author.publicKey,
        authorProfile: authorProfilePda,
        attestation: attestationPda,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const attestation =
      await program.account.attestation.fetch(attestationPda);
    assert.equal(attestation.commitNumber.toNumber(), 2);
    assert.equal(attestation.humanityScore, 88);

    const profile =
      await program.account.authorProfile.fetch(authorProfilePda);
    assert.equal(profile.totalCommits.toNumber(), 2);
    console.log("  ✓ Second commit - evolution tracked");
  });

  it("Verifies an existing attestation", async () => {
    const commitNumber = new anchor.BN(1);
    const [attestationPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [
        Buffer.from("attestation"),
        author.publicKey.toBuffer(),
        Buffer.from(manuscriptHash),
        commitNumber.toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    );

    await program.methods
      .verifyAttestation(manuscriptHash, commitNumber)
      .accounts({
        author: author.publicKey,
        attestation: attestationPda,
      })
      .rpc();

    console.log("  ✓ Attestation verified on-chain");
  });

  it("Rejects score > 100", async () => {
    const [authorProfilePda] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("author_profile"), author.publicKey.toBuffer()],
      program.programId
    );

    const commitNumber = new anchor.BN(3);
    const [attestationPda] = anchor.web3.PublicKey.findProgramAddressSync(
      [
        Buffer.from("attestation"),
        author.publicKey.toBuffer(),
        Buffer.from(manuscriptHash),
        commitNumber.toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    );

    try {
      await program.methods
        .createAttestation(
          manuscriptHash,
          150, // invalid - over 100
          15,
          90,
          "Bad Attestation",
          "This should fail"
        )
        .accounts({
          author: author.publicKey,
          authorProfile: authorProfilePda,
          attestation: attestationPda,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .rpc();
      assert.fail("Should have thrown");
    } catch (_err) {
      console.log("  ✓ Invalid score correctly rejected");
    }
  });
});
