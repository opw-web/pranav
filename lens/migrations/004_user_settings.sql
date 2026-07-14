-- Per-user financial preferences (§WS6). Run in Supabase SQL editor before testing savings.
CREATE TABLE user_settings (
    user_id        UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    monthly_income NUMERIC(14,2),
    savings_goal   NUMERIC(14,2),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_settings_select ON user_settings FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY user_settings_insert ON user_settings FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY user_settings_update ON user_settings FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY user_settings_delete ON user_settings FOR DELETE USING (auth.uid() = user_id);
