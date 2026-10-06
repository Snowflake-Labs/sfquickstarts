/**
 * Factory for CortexAgentClient from @snowflake/cortex-agent-sdk.
 *
 * In SAR (SPCS), reads the OAuth token from /snowflake/session/token.
 * For local dev, falls back to a PAT from the SNOWFLAKE_PAT env var.
 */

import { CortexAgentClient, OAuthAuth } from "@snowflake/cortex-agent-sdk";
import fs from "fs";

const TOKEN_PATH = "/snowflake/session/token";

export function createAgentClient(): CortexAgentClient {
  const account = process.env.SNOWFLAKE_ACCOUNT || "";

  // Check for SPCS OAuth token first
  if (fs.existsSync(TOKEN_PATH)) {
    const token = fs.readFileSync(TOKEN_PATH, "utf-8").trim();
    return new CortexAgentClient({
      account,
      auth: new OAuthAuth(token),
    });
  }

  // Fall back to PAT for local development
  const pat = process.env.SNOWFLAKE_PAT || "";
  return new CortexAgentClient({ account, auth: pat });
}
