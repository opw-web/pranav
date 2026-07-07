"""Pure-Python importer tests — no DB needed. Covers §4.2 detection + §7 Checks 6/7 logic."""
import sys
from datetime import date

sys.path.insert(0, ".")

from app.services import importer

# --- Realistic bank statement fixtures ------------------------------------------------

HDFC = b"""Account Statement
Account No: 50100XXXXXX

Date,Narration,Withdrawal Amt,Deposit Amt,Closing Balance
01/07/2026,UPI-SWIGGY-BANGALORE-482,450.00,,12000.00
02/07/2026,SALARY CREDIT ACME CORP,,50000.00,62000.00
03/07/2026,ATM WDL DELHI,2000.00,,60000.00
"""

ICICI_SIGNED = b"""Txn Date;Transaction Remarks;Amount;Balance
05-07-2026;AMZN MKTP IN 8890;-1299.50;58700.50
06-07-2026;INTEREST PAID;120.00;58820.50
"""


def test_hdfc_debit_credit_detection():
    info = importer.analyze(HDFC)
    assert info["delimiter"] == ","
    assert info["mapping"]["date"] == "Date"
    assert info["mapping"]["desc"] == "Narration"
    assert info["mapping"]["debit"] == "Withdrawal Amt"
    assert info["mapping"]["credit"] == "Deposit Amt"
    assert info["amount_convention"] == "debit_credit_columns"
    assert info["date_format"] == "%d/%m/%Y"
    # header row correctly skipped the two junk lines + blank
    assert info["header"][0] == "Date"

    header, data = importer.parse_rows(
        importer.decode_bytes(HDFC), info["delimiter"], info["header_idx"]
    )
    txns = importer.extract_transactions(
        header, data, info["mapping"], info["date_format"], info["amount_convention"]
    )
    assert len(txns) == 3
    assert txns[0] == {"txn_date": date(2026, 7, 1), "type": "expense", "amount": 450.0,
                       "merchant_raw": "UPI-SWIGGY-BANGALORE-482"}
    assert txns[1]["type"] == "income" and txns[1]["amount"] == 50000.0
    assert txns[2]["type"] == "expense" and txns[2]["amount"] == 2000.0


def test_icici_signed_semicolon():
    info = importer.analyze(ICICI_SIGNED)
    assert info["delimiter"] == ";"
    assert info["amount_convention"] == "signed"
    assert info["mapping"]["date"] == "Txn Date"
    assert info["mapping"]["desc"] == "Transaction Remarks"

    header, data = importer.parse_rows(
        importer.decode_bytes(ICICI_SIGNED), info["delimiter"], info["header_idx"]
    )
    txns = importer.extract_transactions(
        header, data, info["mapping"], info["date_format"], info["amount_convention"]
    )
    assert len(txns) == 2
    assert txns[0]["type"] == "expense" and txns[0]["amount"] == 1299.50
    assert txns[1]["type"] == "income" and txns[1]["amount"] == 120.0


def test_bank_signature_stable_and_distinct():
    a = importer.analyze(HDFC)["signature"]
    b = importer.analyze(HDFC)["signature"]  # same file -> same signature (Check 6)
    c = importer.analyze(ICICI_SIGNED)["signature"]
    assert a == b
    assert a != c


def test_dedupe_hash_identical_rows(  ):
    # Re-importing the same row must produce the same hash -> zero duplicates (Check 7)
    h1 = importer.dedupe_hash("acct-1", date(2026, 7, 1), 450.0, "UPI-SWIGGY-482")
    h2 = importer.dedupe_hash("acct-1", date(2026, 7, 1), 450.0, "UPI-SWIGGY-482")
    h3 = importer.dedupe_hash("acct-1", date(2026, 7, 1), 451.0, "UPI-SWIGGY-482")
    assert h1 == h2
    assert h1 != h3


def test_amount_cleaning():
    assert importer._clean_amount("1,299.50") == 1299.50
    assert importer._clean_amount("₹ 2,000") == 2000.0
    assert importer._clean_amount("(500.00)") == -500.0  # accounting negatives
    assert importer._clean_amount("") is None
    assert importer._clean_amount("-") is None


def test_chunk_bounds():
    # 450 rows, chunk 200 -> pages (0,200,more) (200,400,more) (400,450,done)
    assert importer.chunk_bounds(450, 0) == (0, 200, True)
    assert importer.chunk_bounds(450, 1) == (200, 400, True)
    assert importer.chunk_bounds(450, 2) == (400, 450, False)
    assert importer.chunk_bounds(50, 0) == (0, 50, False)
    assert importer.chunk_bounds(0, 0) == (0, 0, False)


def test_transfer_pair_detection():
    txns = [
        {"txn_date": date(2026, 7, 1), "type": "expense", "amount": 5000.0, "merchant_raw": "TO WALLET"},
        {"txn_date": date(2026, 7, 1), "type": "income", "amount": 5000.0, "merchant_raw": "FROM BANK"},
        {"txn_date": date(2026, 7, 2), "type": "expense", "amount": 300.0, "merchant_raw": "COFFEE"},
    ]
    pairs = importer.find_transfer_pairs(txns)
    assert pairs == [(0, 1)]  # the coffee expense is not paired


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} importer tests passed")
