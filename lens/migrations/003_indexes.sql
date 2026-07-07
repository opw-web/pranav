CREATE INDEX idx_txn_user_date   ON transactions (user_id, txn_date DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_txn_user_cat    ON transactions (user_id, category_id)   WHERE is_deleted = FALSE;
CREATE INDEX idx_txn_dedupe      ON transactions (user_id, dedupe_hash);
CREATE INDEX idx_txn_merchant    ON transactions (user_id, merchant_clean);
CREATE INDEX idx_rules_user      ON categorization_rules (user_id, priority);
CREATE INDEX idx_merchant_seed   ON merchant_seed (pattern);
