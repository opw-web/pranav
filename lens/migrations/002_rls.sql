ALTER TABLE accounts             ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories           ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions         ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_tags     ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorization_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_series     ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets              ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_batches       ENABLE ROW LEVEL SECURITY;
ALTER TABLE column_mappings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_recaps       ENABLE ROW LEVEL SECURITY;

-- ACCOUNTS
CREATE POLICY accounts_select ON accounts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY accounts_insert ON accounts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY accounts_update ON accounts FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY accounts_delete ON accounts FOR DELETE USING (auth.uid() = user_id);

-- CATEGORIES
CREATE POLICY categories_select ON categories FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY categories_insert ON categories FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY categories_update ON categories FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY categories_delete ON categories FOR DELETE USING (auth.uid() = user_id);

-- TAGS
CREATE POLICY tags_select ON tags FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY tags_insert ON tags FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY tags_update ON tags FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY tags_delete ON tags FOR DELETE USING (auth.uid() = user_id);

-- TRANSACTIONS
CREATE POLICY txn_select ON transactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY txn_insert ON transactions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY txn_update ON transactions FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY txn_delete ON transactions FOR DELETE USING (auth.uid() = user_id);

-- TRANSACTION_TAGS (no user_id column; scope via parent transaction)
CREATE POLICY txn_tags_select ON transaction_tags FOR SELECT USING (
    EXISTS (SELECT 1 FROM transactions t WHERE t.id = transaction_id AND t.user_id = auth.uid())
);
CREATE POLICY txn_tags_insert ON transaction_tags FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM transactions t WHERE t.id = transaction_id AND t.user_id = auth.uid())
);
CREATE POLICY txn_tags_update ON transaction_tags FOR UPDATE USING (
    EXISTS (SELECT 1 FROM transactions t WHERE t.id = transaction_id AND t.user_id = auth.uid())
);
CREATE POLICY txn_tags_delete ON transaction_tags FOR DELETE USING (
    EXISTS (SELECT 1 FROM transactions t WHERE t.id = transaction_id AND t.user_id = auth.uid())
);

-- CATEGORIZATION_RULES
CREATE POLICY rules_select ON categorization_rules FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY rules_insert ON categorization_rules FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY rules_update ON categorization_rules FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY rules_delete ON categorization_rules FOR DELETE USING (auth.uid() = user_id);

-- RECURRING_SERIES
CREATE POLICY recurring_select ON recurring_series FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY recurring_insert ON recurring_series FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY recurring_update ON recurring_series FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY recurring_delete ON recurring_series FOR DELETE USING (auth.uid() = user_id);

-- BUDGETS
CREATE POLICY budgets_select ON budgets FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY budgets_insert ON budgets FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY budgets_update ON budgets FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY budgets_delete ON budgets FOR DELETE USING (auth.uid() = user_id);

-- IMPORT_BATCHES
CREATE POLICY import_batches_select ON import_batches FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY import_batches_insert ON import_batches FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY import_batches_update ON import_batches FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY import_batches_delete ON import_batches FOR DELETE USING (auth.uid() = user_id);

-- COLUMN_MAPPINGS
CREATE POLICY column_mappings_select ON column_mappings FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY column_mappings_insert ON column_mappings FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY column_mappings_update ON column_mappings FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY column_mappings_delete ON column_mappings FOR DELETE USING (auth.uid() = user_id);

-- MONTHLY_RECAPS
CREATE POLICY recaps_select ON monthly_recaps FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY recaps_insert ON monthly_recaps FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY recaps_update ON monthly_recaps FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY recaps_delete ON monthly_recaps FOR DELETE USING (auth.uid() = user_id);

-- merchant_seed is global read-only:
ALTER TABLE merchant_seed ENABLE ROW LEVEL SECURITY;
CREATE POLICY seed_read ON merchant_seed FOR SELECT USING (true);
