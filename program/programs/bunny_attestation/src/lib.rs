use anchor_lang::prelude::*;

declare_id!("4ATURpD3Aeq5FdnGDppFvdQG5xCaLStsopPrADJHK1nt");

#[program]
pub mod bunny_attestation {
    use super::*;

    /// Creates a new attestation for a manuscript.
    /// Stores the SHA-256 hash, humanity score, and metadata on-chain.
    pub fn create_attestation(
        ctx: Context<CreateAttestation>,
        manuscript_hash: [u8; 32],
        humanity_score: u8,
        ai_score: u8,
        temporal_score: u8,
        title: String,
        commit_message: String,
    ) -> Result<()> {
        require!(title.len() <= 128, BunnyError::TitleTooLong);
        require!(commit_message.len() <= 256, BunnyError::CommitMessageTooLong);
        require!(humanity_score <= 100, BunnyError::InvalidScore);
        require!(ai_score <= 100, BunnyError::InvalidScore);
        require!(temporal_score <= 100, BunnyError::InvalidScore);

        let attestation = &mut ctx.accounts.attestation;
        let clock = Clock::get()?;

        attestation.author = ctx.accounts.author.key();
        attestation.manuscript_hash = manuscript_hash;
        attestation.humanity_score = humanity_score;
        attestation.ai_score = ai_score;
        attestation.temporal_score = temporal_score;
        attestation.title = title;
        attestation.commit_message = commit_message;
        attestation.timestamp = clock.unix_timestamp;
        attestation.commit_number = ctx.accounts.author_profile.total_commits + 1;
        attestation.bump = ctx.bumps.attestation;

        // Update author profile
        let profile = &mut ctx.accounts.author_profile;
        profile.author = ctx.accounts.author.key();
        profile.total_commits += 1;
        profile.last_commit_timestamp = clock.unix_timestamp;
        profile.bump = ctx.bumps.author_profile;

        emit!(AttestationCreated {
            author: ctx.accounts.author.key(),
            manuscript_hash,
            humanity_score,
            commit_number: attestation.commit_number,
            timestamp: clock.unix_timestamp,
        });

        msg!(
            "Attestation created: score={}, commit=#{}",
            humanity_score,
            attestation.commit_number
        );

        Ok(())
    }

    /// Initializes a new author profile. Called once per author.
    pub fn initialize_profile(ctx: Context<InitializeProfile>) -> Result<()> {
        let profile = &mut ctx.accounts.author_profile;
        profile.author = ctx.accounts.author.key();
        profile.total_commits = 0;
        profile.last_commit_timestamp = 0;
        profile.bump = ctx.bumps.author_profile;

        msg!("Author profile initialized for {}", ctx.accounts.author.key());
        Ok(())
    }

    /// Verifies that an attestation exists for the given parameters.
    /// This is a read-only check — useful for on-chain verification by other programs.
    pub fn verify_attestation(
        ctx: Context<VerifyAttestation>,
        _manuscript_hash: [u8; 32],
        _commit_number: u64,
    ) -> Result<()> {
        let attestation = &ctx.accounts.attestation;
        msg!(
            "Attestation verified: author={}, score={}, timestamp={}",
            attestation.author,
            attestation.humanity_score,
            attestation.timestamp
        );
        Ok(())
    }
}

// ─── Accounts ───────────────────────────────────────────────────────

#[derive(Accounts)]
#[instruction(
    manuscript_hash: [u8; 32],
    humanity_score: u8,
    ai_score: u8,
    temporal_score: u8,
    title: String,
    commit_message: String,
)]
pub struct CreateAttestation<'info> {
    #[account(mut)]
    pub author: Signer<'info>,

    #[account(
        init_if_needed,
        payer = author,
        space = AuthorProfile::SIZE,
        seeds = [b"author_profile", author.key().as_ref()],
        bump,
    )]
    pub author_profile: Account<'info, AuthorProfile>,

    #[account(
        init,
        payer = author,
        space = Attestation::size(&title, &commit_message),
        seeds = [
            b"attestation",
            author.key().as_ref(),
            manuscript_hash.as_ref(),
            &(author_profile.total_commits + 1).to_le_bytes(),
        ],
        bump,
    )]
    pub attestation: Account<'info, Attestation>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct InitializeProfile<'info> {
    #[account(mut)]
    pub author: Signer<'info>,

    #[account(
        init,
        payer = author,
        space = AuthorProfile::SIZE,
        seeds = [b"author_profile", author.key().as_ref()],
        bump,
    )]
    pub author_profile: Account<'info, AuthorProfile>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(manuscript_hash: [u8; 32], commit_number: u64)]
pub struct VerifyAttestation<'info> {
    /// CHECK: This is the author's pubkey used for PDA derivation only.
    pub author: UncheckedAccount<'info>,

    #[account(
        seeds = [
            b"attestation",
            author.key().as_ref(),
            manuscript_hash.as_ref(),
            &commit_number.to_le_bytes(),
        ],
        bump = attestation.bump,
    )]
    pub attestation: Account<'info, Attestation>,
}

// ─── State ──────────────────────────────────────────────────────────

#[account]
pub struct Attestation {
    /// The author's wallet pubkey
    pub author: Pubkey,
    /// SHA-256 hash of the manuscript content
    pub manuscript_hash: [u8; 32],
    /// Final humanity score (0-100, higher = more likely human)
    pub humanity_score: u8,
    /// AI detection score from DeBERTa (0-100, higher = more likely AI)
    pub ai_score: u8,
    /// Temporal evolution score (0-100, higher = more natural evolution)
    pub temporal_score: u8,
    /// Document title
    pub title: String,
    /// Commit message describing changes
    pub commit_message: String,
    /// Unix timestamp of attestation
    pub timestamp: i64,
    /// Sequential commit number for this author
    pub commit_number: u64,
    /// PDA bump seed
    pub bump: u8,
}

impl Attestation {
    /// Calculate account size dynamically based on string lengths
    pub fn size(title: &str, commit_message: &str) -> usize {
        8 +        // anchor discriminator
        32 +       // author pubkey
        32 +       // manuscript_hash
        1 +        // humanity_score
        1 +        // ai_score
        1 +        // temporal_score
        4 + title.len() +          // title (4 bytes length prefix + data)
        4 + commit_message.len() + // commit_message
        8 +        // timestamp
        8 +        // commit_number
        1 +        // bump
        64         // padding for safety
    }
}

#[account]
pub struct AuthorProfile {
    /// The author's wallet pubkey
    pub author: Pubkey,
    /// Total number of commits/attestations made
    pub total_commits: u64,
    /// Timestamp of the last commit
    pub last_commit_timestamp: i64,
    /// PDA bump seed
    pub bump: u8,
}

impl AuthorProfile {
    pub const SIZE: usize = 8 + 32 + 8 + 8 + 1 + 32; // discriminator + fields + padding
}

// ─── Events ─────────────────────────────────────────────────────────

#[event]
pub struct AttestationCreated {
    pub author: Pubkey,
    pub manuscript_hash: [u8; 32],
    pub humanity_score: u8,
    pub commit_number: u64,
    pub timestamp: i64,
}

// ─── Errors ─────────────────────────────────────────────────────────

#[error_code]
pub enum BunnyError {
    #[msg("Title must be 128 characters or less")]
    TitleTooLong,
    #[msg("Commit message must be 256 characters or less")]
    CommitMessageTooLong,
    #[msg("Score must be between 0 and 100")]
    InvalidScore,
}
