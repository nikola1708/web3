"""
Bunny - Solana Relayer Service
Submits attestations on-chain without requiring the writer to have a wallet.
No SOLANA_PRIVATE_KEY configured → gracefully skips on-chain submission.
"""

from app.config import settings


async def submit_attestation_onchain(
    manuscript_hash_hex: str,
    humanity_score: int,
    ai_score: int,
    temporal_score: int,
    title: str,
    commit_message: str,
    author_id: str,
) -> dict:
    if not settings.SOLANA_PRIVATE_KEY:
        return {
            "status": "skipped",
            "reason": "No SOLANA_PRIVATE_KEY configured. Set it in .env to enable on-chain attestation.",
            "tx_signature": None,
        }

    try:
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solana.rpc.async_api import AsyncClient
        import base58

        relayer = Keypair.from_bytes(base58.b58decode(settings.SOLANA_PRIVATE_KEY))
        program_id = Pubkey.from_string(settings.PROGRAM_ID)

        async with AsyncClient(settings.SOLANA_RPC_URL) as client:
            balance = await client.get_balance(relayer.pubkey())
            if balance.value < 10_000_000:
                return {
                    "status": "error",
                    "reason": f"Relayer balance too low ({balance.value} lamports). Fund with devnet SOL.",
                    "tx_signature": None,
                }

        # Full AnchorPy instruction building requires deployed program IDL.
        # Once program is deployed, wire up here.
        return {
            "status": "pending_deploy",
            "reason": "Relayer funded. Deploy Anchor program and update PROGRAM_ID to enable attestations.",
            "tx_signature": None,
            "intent": {
                "relayer": str(relayer.pubkey()),
                "program_id": str(program_id),
                "manuscript_hash": manuscript_hash_hex,
                "humanity_score": humanity_score,
            },
        }

    except ImportError:
        return {
            "status": "skipped",
            "reason": "Solana SDK not installed. Run: pip install solana solders anchorpy base58",
            "tx_signature": None,
        }
    except Exception as e:
        return {"status": "error", "reason": str(e), "tx_signature": None}


async def verify_attestation_onchain(manuscript_hash_hex: str, author_pubkey: str, commit_number: int) -> dict:
    if not settings.SOLANA_PRIVATE_KEY:
        return {"verified": False, "reason": "No Solana connection configured"}
    try:
        from solders.pubkey import Pubkey
        from solana.rpc.async_api import AsyncClient

        program_id = Pubkey.from_string(settings.PROGRAM_ID)
        author_pk = Pubkey.from_string(author_pubkey) if author_pubkey else program_id
        hash_bytes = bytes.fromhex(manuscript_hash_hex)
        seeds = [b"attestation", bytes(author_pk), hash_bytes, commit_number.to_bytes(8, "little")]
        pda, _ = Pubkey.find_program_address(seeds, program_id)

        async with AsyncClient(settings.SOLANA_RPC_URL) as client:
            account = await client.get_account_info(pda)
            if account.value:
                return {"verified": True, "pda": str(pda)}
            return {"verified": False, "pda": str(pda), "reason": "Account not found on-chain"}
    except Exception as e:
        return {"verified": False, "reason": str(e)}
