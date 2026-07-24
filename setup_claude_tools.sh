#!/usr/bin/env bash
# =============================================================================
# setup_claude_tools.sh — RunPod / headless Linux setup for Claude Code
#
# PERSISTENCE
# -----------
# ~/root      is ephemeral — wiped on pod restart.
# ~/workspace is the persistent network volume.
#
# This script stores Claude Code's config in ~/workspace/.claude and symlinks
# ~/.claude -> ~/workspace/.claude. The symlink is recreated every time this
# script runs, so the fix for a pod restart is simply:
#
#   bash ~/workspace/setup_claude_tools.sh --skip-all
#
# Add that as your RunPod "Start Command" in the pod template to make it
# fully automatic. Or run it manually after each restart (takes <1 second).
#
# TOOLS
# -----
#   0. Claude Code   (native binary)
#   1. Auth          (CLAUDE_CODE_OAUTH_TOKEN for Max/Pro)
#   2. Node.js       (required by caveman hooks)
#   3. Plugins       (caveman, superpowers, context-mode)
#   4. MCP           (codebase-memory-mcp — knowledge graph)
#   5. RTK           (Rust Token Killer — token compression)
#   6. uv            (Python package manager)
#   7. Permissions   (~/.claude/settings.json)
#
# Safe to re-run — all steps are idempotent.
# Assumes root. Tested on RunPod Ubuntu 22.04.
#
# Usage:
#   bash setup_claude_tools.sh                   # full install
#   bash setup_claude_tools.sh --skip-all        # symlink only (post-restart)
#   bash setup_claude_tools.sh --skip-claude ... # skip individual steps
# =============================================================================

set -euo pipefail

# ── helpers ───────────────────────────────────────────────────────────────────
step() { echo ""; echo "━━━ $* ━━━"; }
ok()   { echo "  ✓ $*"; }
warn() { echo "  ⚠ $*"; }
info() { echo "  · $*"; }
fail() { echo "  ✗ $*"; }

# merge_settings [jq-args...] EXPR
# Merges a jq expression into settings.json, creating the file if needed.
merge_settings() {
    local tmp
    tmp=$(mktemp)
    if [ -f "$SETTINGS" ]; then
        jq "$@" "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
    else
        jq -n "$@" > "$SETTINGS"
    fi
}

# =============================================================================
# PERSISTENCE — runs unconditionally on every script invocation
# Creates ~/workspace/.claude and symlinks ~/.claude to it.
# This is the only thing needed after a pod restart.
# =============================================================================
mkdir -p ~/workspace/.claude

# Migrate real ~/.claude directory to ~/workspace if this is first run
if [ -d ~/root/.claude ] && [ ! -L ~/root/.claude ]; then
    cp -rn ~/root/.claude/. ~/workspace/.claude/ 2>/dev/null || true
    rm -rf ~/root/.claude
fi

# (Re)create the symlink — safe to run on every start
[ ! -e ~/root/.claude ] && ln -s ~/workspace/.claude ~/root/.claude

# Set CLAUDE_CONFIG_DIR for this session
export CLAUDE_CONFIG_DIR=~/workspace/.claude

# Ensure persistent tool paths are on PATH for this session
export CARGO_HOME=~/workspace/.cargo
export PATH="~/workspace/.local/bin:~/workspace/.cargo/bin:$PATH"

# ── flags ─────────────────────────────────────────────────────────────────────
SKIP_CLAUDE=false; SKIP_AUTH=false;    SKIP_NODE=false
SKIP_PLUGINS=false; SKIP_MCP=false;   SKIP_RTK=false
SKIP_UV=false;      SKIP_PERMS=false

for arg in "$@"; do case $arg in
    --skip-all)     SKIP_CLAUDE=true; SKIP_AUTH=true; SKIP_NODE=true
                    SKIP_PLUGINS=true; SKIP_MCP=true; SKIP_RTK=true
                    SKIP_UV=true; SKIP_PERMS=true ;;
    --skip-claude)  SKIP_CLAUDE=true  ;;
    --skip-auth)    SKIP_AUTH=true    ;;
    --skip-node)    SKIP_NODE=true    ;;
    --skip-plugins) SKIP_PLUGINS=true ;;
    --skip-mcp)     SKIP_MCP=true     ;;
    --skip-rtk)     SKIP_RTK=true     ;;
    --skip-uv)      SKIP_UV=true      ;;
    --skip-perms)   SKIP_PERMS=true   ;;
esac; done

# settings.json path — used by multiple steps below
SETTINGS="$HOME/.claude/settings.json"
mkdir -p "$(dirname "$SETTINGS")"

command -v jq &>/dev/null || apt-get install -y jq -qq 2>/dev/null

echo ""
echo "  Claude Code — RunPod Setup"
echo "  ══════════════════════════"

# =============================================================================
# 0. Claude Code — native binary, no Node.js required
# =============================================================================
if [ "$SKIP_CLAUDE" = false ]; then
    step "0/7  Claude Code"
    if command -v claude &>/dev/null; then
        ok "already installed: $(claude --version 2>/dev/null)"
    else
        info "installing via native installer..."
        curl -fsSL https://claude.ai/install.sh | bash
        export PATH="~/workspace/.local/bin:$HOME/.local/bin:$HOME/.claude/bin:$PATH"
        grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null \
            || echo 'export PATH="~/workspace/.local/bin:$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        command -v claude &>/dev/null \
            && ok "installed: $(claude --version 2>/dev/null)" \
            || warn "not in PATH yet — run: source ~/.bashrc"
    fi
fi

# =============================================================================
# 1. Auth — CLAUDE_CODE_OAUTH_TOKEN
#
# Generate once on your local machine: claude setup-token
# Set as a RunPod environment variable, or paste below.
# Valid for 1 year. Uses your Max/Pro subscription quota.
# =============================================================================
if [ "$SKIP_AUTH" = false ]; then
    step "1/7  Auth"
    if [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
        ok "CLAUDE_CODE_OAUTH_TOKEN already set"
    else
        info "paste your token from 'claude setup-token' (Enter to skip):"
        read -rs token
        echo ""
        if [ -n "$token" ]; then
            echo "export CLAUDE_CODE_OAUTH_TOKEN=\"$token\"" >> "$HOME/.bashrc"
            export CLAUDE_CODE_OAUTH_TOKEN="$token"
            ok "saved to ~/.bashrc"
        else
            warn "skipped — set CLAUDE_CODE_OAUTH_TOKEN before running Claude Code"
        fi
    fi
fi

# =============================================================================
# 2. Node.js 22 LTS
#
# Required at runtime by caveman's SessionStart hooks (JS files).
# =============================================================================
if [ "$SKIP_NODE" = false ]; then
    step "2/7  Node.js"
    if command -v node &>/dev/null; then
        ok "already installed: $(node --version)"
    else
        info "installing Node.js 22 LTS via NodeSource..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null 2>&1
        apt-get install -y nodejs -qq
        ok "installed: $(node --version)"
    fi
fi

# =============================================================================
# 3. Plugins
#
#   caveman       — compresses Claude's output ~65% fewer tokens
#   superpowers   — enforces brainstorm → spec → plan → TDD before coding
#   context-mode  — sandboxes tool output; rebuilds session state after compaction
#
# Strategy:
#   - caveman:      standalone hook installer (sets up JS hooks + status badge)
#                   AND plugin registration (so /plugins shows it)
#   - superpowers:  claude plugin install CLI
#   - context-mode: claude plugin install CLI
#
# Note: plugin CLI calls may silently fail if Claude Code hasn't been
# authenticated yet. If /plugins shows nothing after first launch, run:
#   claude plugin marketplace add <repo> && claude plugin install <id> --scope user
# =============================================================================
if [ "$SKIP_PLUGINS" = false ]; then
    step "3/7  Plugins"

    if ! command -v claude &>/dev/null; then
        warn "claude not in PATH — skipping (install Claude Code first)"
    else
        # Register all marketplaces first
        info "registering marketplaces..."
        claude plugin marketplace add JuliusBrussee/caveman       2>/dev/null || true
        claude plugin marketplace add obra/superpowers-marketplace 2>/dev/null || true
        claude plugin marketplace add mksglu/context-mode         2>/dev/null || true

        # caveman: run standalone installer for hooks/badge AND register as plugin
        info "installing caveman..."
        curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/hooks/install.sh \
            | bash 2>/dev/null \
            && ok "caveman hooks + badge installed" \
            || warn "caveman standalone installer failed"
        # Also register as a plugin so it appears in /plugins
        claude plugin install caveman@caveman --scope user 2>/dev/null \
            && ok "caveman registered as plugin" \
            || warn "caveman plugin registration failed — run inside Claude Code: /plugin install caveman@caveman"

        # superpowers and context-mode
        for plugin_id in "superpowers@superpowers-marketplace" "context-mode@context-mode"; do
            name="${plugin_id%%@*}"
            info "installing $name..."
            claude plugin install "$plugin_id" --scope user 2>/dev/null \
                && ok "$name" \
                || warn "$name install failed — run inside Claude Code: /plugin install $plugin_id"
        done

        info "restart Claude Code after setup, then verify with /plugins"
    fi
fi

# =============================================================================
# 4. codebase-memory-mcp
#
# Indexes your codebase into a SQLite knowledge graph via tree-sitter ASTs.
# Downloads a portable (musl/static) pre-built binary — no Go or gcc needed.
# Registered directly in ~/.claude/settings.json under mcpServers.
# =============================================================================
if [ "$SKIP_MCP" = false ]; then
    step "4/7  codebase-memory-mcp"
    MCP_BIN="~/workspace/.local/bin/codebase-memory-mcp"

    if [ -x "$MCP_BIN" ]; then
        ok "already installed at $MCP_BIN"
    else
        info "downloading portable binary (musl-linked, no glibc dependency)..."
        mkdir -p ~/workspace/.local/bin
        # Download the portable variant directly — the standard binary requires
        # a newer glibc than RunPod Ubuntu 22.04 provides.
        # Portable binary is a raw file in release assets (no tar.gz wrapper).
        curl -fsSL             "https://github.com/DeusData/codebase-memory-mcp/releases/latest/download/codebase-memory-mcp-linux-amd64-portable"             -o "$MCP_BIN"
        chmod 755 "$MCP_BIN"
        ok "installed to $MCP_BIN"
    fi

    if [ -x "$MCP_BIN" ]; then
        if ! grep -q "codebase-memory-mcp" "$SETTINGS" 2>/dev/null; then
            merge_settings --arg bin "$MCP_BIN" \
                '.mcpServers["codebase-memory-mcp"] = {type:"stdio", command:$bin}'
            ok "registered in settings.json"
        else
            info "already registered in settings.json"
        fi
    fi

    # Routing hint so Claude prefers graph tools over grep
    CLAUDE_MD="~/workspace/.claude/CLAUDE.md"
    if ! grep -q "codebase-memory-mcp" "$CLAUDE_MD" 2>/dev/null; then
        cat >> "$CLAUDE_MD" << 'HINT'

## Codebase Memory (codebase-memory-mcp)

Prefer graph tools over grep/Explore for structural questions — one query vs thousands of tokens.

- Start of task: `index_repository` (incremental, fast after first run)
- Who calls X?   `trace_call_path(function_name="X", direction="inbound")`
- What does X call? `trace_call_path(function_name="X", direction="outbound")`
- Find by name:  `search_graph(label="Function", name_pattern=".*Pattern.*")`
- Dead code:     `search_graph(label="Function", relationship="CALLS", direction="inbound", max_degree=0, exclude_entry_points=true)`
- REST routes:   `search_graph(label="Route")`
- Custom:        `query_graph(query="MATCH ...")` with Cypher

Use grep/Glob for text search — the graph indexes structure, not content.
HINT
        ok "routing hint added to CLAUDE.md"
    else
        info "CLAUDE.md hint already present"
    fi
fi

# =============================================================================
# 5. RTK — Rust Token Killer
#
# Compresses input tokens before they enter the context window.
# Pair with caveman (output compression) and context-mode (tool sandboxing).
# =============================================================================
if [ "$SKIP_RTK" = false ]; then
    step "5/7  RTK"
    if command -v rtk &>/dev/null; then
        ok "already installed: $(rtk --version 2>/dev/null)"
    else
        export CARGO_HOME=~/workspace/.cargo
        export PATH="~/workspace/.cargo/bin:$PATH"
        curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
        command -v rtk &>/dev/null \
            && ok "installed: $(rtk --version 2>/dev/null)" \
            || warn "not in PATH — restart shell"
    fi

    if command -v rtk &>/dev/null; then
        RTK_BIN=$(command -v rtk)
        HOOKS_DIR="$(dirname "$SETTINGS")/hooks"

        # --auto-patch: non-interactive; RTK writes hook entry + RTK.md + settings.json itself
        rtk init -g --auto-patch 2>/dev/null \
            && ok "RTK configured (hook + RTK.md + settings.json)" \
            || info "RTK already configured"

        # Approach A: patch bare 'rtk hook claude' → full path so hooks survive restricted PATH
        tmp=$(mktemp)
        jq --arg bin "$RTK_BIN" '
            walk(if type == "object" and .command? == "rtk hook claude"
                 then .command = ($bin + " hook claude")
                 else . end)
        ' "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"

        # Test approach A: pipe a fake Bash tool call through the hook
        TEST_INPUT='{"tool_name":"Bash","tool_input":{"command":"git status"}}'
        TEST_OUT=$(printf '%s' "$TEST_INPUT" | "$RTK_BIN" hook claude 2>/dev/null)
        if printf '%s' "$TEST_OUT" | jq -e '.tool_input.command' &>/dev/null; then
            ok "RTK hook verified (approach A: native binary)"
        else
            warn "RTK native hook failed — falling back to custom shell script (approach B)"

            # Approach B: write a self-contained shell script that uses the full RTK path
            mkdir -p "$HOOKS_DIR"
            RTK_HOOK="$HOOKS_DIR/rtk-rewrite.sh"
            cat > "$RTK_HOOK" << HOOK
#!/usr/bin/env bash
# RTK PreToolUse hook — rewrites Bash commands through rtk proxy
input=\$(cat)
cmd=\$(printf '%s' "\$input" | jq -r '.tool_input.command // empty')
[[ -z "\$cmd" || "\$cmd" == "${RTK_BIN} "* || "\$cmd" == "rtk "* ]] && exit 0
printf '{"tool_input":{"command":%s}}' "\$(printf '${RTK_BIN} %s' "\$cmd" | jq -Rs .)"
HOOK
            chmod +x "$RTK_HOOK"

            # Replace RTK's hook entry with the script path
            tmp=$(mktemp)
            jq --arg script "$RTK_HOOK" '
                walk(if type == "object" and (.command? | test("rtk hook claude|hook claude"))
                     then .command = $script
                     else . end)
            ' "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
            ok "RTK fallback hook installed: $RTK_HOOK"
        fi
    fi
fi

# =============================================================================
# 6. uv — Python package manager
#
# Not required now, but needed if you add Python-based MCP servers later.
# =============================================================================
if [ "$SKIP_UV" = false ]; then
    step "6/7  uv"
    if command -v uv &>/dev/null; then
        ok "already installed: $(uv --version)"
    else
        UV_INSTALL_DIR=~/workspace/.local/bin curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="~/workspace/.local/bin:$PATH"
        command -v uv &>/dev/null \
            && ok "installed: $(uv --version)" \
            || warn "not in PATH — restart shell"
    fi
fi

# =============================================================================
# 7. Permissions — ~/.claude/settings.json
#
# Grants Claude read access to home + any extra mounted volumes.
# Uses merge_settings so existing mcpServers/hooks entries are preserved.
# =============================================================================
if [ "$SKIP_PERMS" = false ]; then
    step "7/7  Permissions"

    info "extra read paths (e.g. ~/workspace/data) — one per line, Enter to finish:"
    EXTRA_DIRS=()
    while IFS= read -r -p "  path: " dir; do
        [[ -z "$dir" ]] && break
        EXTRA_DIRS+=("$dir")
    done

    if [ ${#EXTRA_DIRS[@]} -gt 0 ]; then
        EXTRA_JSON=$(printf '%s\n' "${EXTRA_DIRS[@]}" | jq -R . | jq -s .)
    else
        EXTRA_JSON='[]'
    fi

    ALLOW=$(jq -n --arg home "$HOME" --argjson extra "$EXTRA_JSON" \
        '["Read(**)", "Read(\($home)/**)" ] + ($extra | map("Read(\(.)/**)"))')

    merge_settings --argjson allow "$ALLOW" '.permissions.allow = $allow'

    ok "permissions written to settings.json"
    [ ${#EXTRA_DIRS[@]} -gt 0 ] && info "extra paths: ${EXTRA_DIRS[*]}"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "  ══════════════════════════"
echo "  Done"
echo "  ══════════════════════════"
echo ""
echo "  Status:"
command -v claude &>/dev/null \
    && echo "  ✓ claude   $(claude --version 2>/dev/null)" \
    || echo "  ✗ claude   (not in PATH — source ~/.bashrc)"
[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] \
    && echo "  ✓ auth     token set" \
    || echo "  ✗ auth     CLAUDE_CODE_OAUTH_TOKEN not set"
command -v node &>/dev/null \
    && echo "  ✓ node     $(node --version)" \
    || echo "  ✗ node     (not installed)"
[ -x "~/workspace/.local/bin/codebase-memory-mcp" ] \
    && echo "  ✓ mcp      codebase-memory-mcp" \
    || echo "  ✗ mcp      not installed"
command -v rtk &>/dev/null \
    && echo "  ✓ rtk      $(rtk --version 2>/dev/null)" \
    || echo "  ✗ rtk      (not in PATH)"
command -v uv &>/dev/null \
    && echo "  ✓ uv       $(uv --version)" \
    || echo "  ✗ uv       (not in PATH)"
echo ""
echo "  Next:"
echo "  1. source ~/.bashrc"
echo "  2. cd your-project && claude   (complete OAuth login on first launch)"
echo "  3. /plugins  → verify caveman, superpowers, context-mode"
echo "  4. /mcp      → verify codebase-memory-mcp"
echo "  5. 'index this project'"
echo ""