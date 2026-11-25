author: Yossi Eliaz
id: coco-sandboxed-shell-with-openshell
language: en
summary: Run every shell command that CoCo CLI issues in a local OpenShell sandbox instead of on your machine, or run CoCo itself inside the sandbox with only your Snowflake account reachable.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-code
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/coco-skills/tree/main/plugins/sandboxed-shell

# Run CoCo CLI Shell Commands in an OpenShell Sandbox
<!-- ------------------------ -->
## Overview

By default, CoCo CLI runs shell commands directly on your machine. It has two sandbox
options of its own: [`/sandbox`](https://docs.snowflake.com/en/user-guide/cortex-code/sandbox)
restricts commands with your operating system's sandbox and still runs them on your machine,
and [`cortex --cloud`](https://docs.snowflake.com/en/user-guide/cortex-code/cloud-sandbox)
runs them in a Snowflake-managed container on a mounted Snowflake workspace, not your local
files. This guide shows a third option, for teams that use
[NVIDIA OpenShell](https://docs.nvidia.com/openshell/latest/): a plugin that sends each
shell command CoCo issues to an OpenShell sandbox holding a copy of your local project; if
no sandbox can be reached, the command does not run. Then you go one step further and run
CoCo itself inside an OpenShell sandbox whose network policy allows only your Snowflake
account.

### Prerequisites
- CoCo CLI installed and connected to your Snowflake account
- macOS or Linux, with `python3` 3.9 or newer
- Docker, for the OpenShell gateway

### What You'll Learn
- How a `PreToolUse` hook routes CoCo's shell commands into a sandbox
- What is copied into the sandbox and what never comes back
- How to give CoCo no shell except the sandbox, for a team
- How to run CoCo inside OpenShell without placing your token in the sandbox

### What You'll Need
- A Snowflake user with CoCo, and a programmatic access token for the last section
- [OpenShell](https://docs.nvidia.com/openshell/latest/) installed

### What You'll Build
- A CoCo session whose shell commands run in a Linux sandbox on your machine
- A CoCo session that runs entirely inside OpenShell and can reach only your account

<!-- ------------------------ -->
## Start OpenShell

Install OpenShell and start a gateway as described in its documentation, then check it:

```bash
openshell status
```

The output shows `Status: Connected`. The plugin creates one sandbox per project the first
time CoCo runs a shell command there.

<!-- ------------------------ -->
## Install the Plugin

Install the plugin from the Snowflake-Labs coco-skills repository and check it:

```bash
cortex plugin install Snowflake-Labs/coco-skills/plugins/sandboxed-shell
cortex plugin validate sandboxed-shell
```

The second command prints `Plugin 'sandboxed-shell' is valid.`

<!-- ------------------------ -->
## Run a Sandboxed Command

Start CoCo in a project directory and ask it to run a command:

```bash
cd my-project
cortex
```

```
Run uname -s, pwd and ls -a
```

The command runs in the sandbox, so it prints `Linux`, a path under `/sandbox`, and your
project files. Files the command writes come back to your project. Names that look like
secrets, such as `.env`, `*.pem` or `connections.toml`, are never copied into the sandbox,
and nothing under `.git` except plain repository data comes back from it, so a command in
the sandbox cannot install a Git hook on your machine.

CoCo shows the rewritten command: a call to the plugin's runner, with your command quoted
at the end. Subagents and background commands go through the same path, and `kill_shell`
and time limits stop the command inside the sandbox.

<!-- ------------------------ -->
## Enforce the Sandbox

A user can switch a plugin off. To leave the agent no shell except the sandbox, an
administrator denies the built-in shell tool in CoCo's managed settings and deploys the
plugin's MCP server, whose `sandbox_exec` tool runs commands through the same runner. The
plugin ships both files as examples in `plugins/sandboxed-shell/managed/`. Check the managed-settings
file before rolling it out:

```bash
cortex managed-settings encode managed-settings.example.json
```

Start CoCo in the project directory: CoCo starts MCP servers in the directory it was
launched from.

<!-- ------------------------ -->
## Run CoCo Inside OpenShell

The plugin moves shell commands. To move everything CoCo does into the sandbox, run CoCo
itself there. The plugin has two scripts for this:

```bash
git clone https://github.com/Snowflake-Labs/coco-skills
cd coco-skills/plugins/sandboxed-shell
```

Once, store your token in the OpenShell gateway rather than in any sandbox:

```bash
SNOWFLAKE_ACCOUNT=myorg-myaccount SNOWFLAKE_TOKEN=<token> openshell/snowflake-provider.sh
```

Then run a prompt:

```bash
PROVIDER=snowflake SNOWFLAKE_ACCOUNT=myorg-myaccount SNOWFLAKE_USER=me@example.com \
  openshell/coco-in-openshell.sh "Run uname -s and list the files"
```

The script downloads Snowflake's Linux build of CoCo, checks its checksum, and runs your
prompt in a sandbox that can reach one host, your account. `SNOWFLAKE_USER` is your login
name; for users created through single sign-on that is usually your email.

The sandbox sees only a placeholder for the token. OpenShell's proxy puts the real token
into the body of the sign-in request, and nowhere else, as declared in
`openshell/providers/snowflake.yaml`. Keep that file pinned to your account host.

<!-- ------------------------ -->
## Know the Limits

- Use either this plugin or CoCo's `/sandbox` in a session. Running both together is not
  tested.
- If the plugin's hook does not answer within its time limit (60 seconds), CoCo runs the
  original command on your machine. The hook normally answers in about 50 milliseconds.
- CoCo checks permission rules written for specific commands, such as `bash(git *)`,
  against the rewritten command, so they stop matching. Rules for the whole `bash` tool
  still work.
- Files a command changes in the project do come back. Review changes to scripts and build
  files before you run them outside the sandbox.
- When CoCo runs inside OpenShell, the session token Snowflake returns after sign-in is
  real, and the placeholder is replaced anywhere in the sign-in request. Use a short-lived
  token restricted to one role.

<!-- ------------------------ -->
## Conclusion And Resources

You moved CoCo's shell commands into a local sandbox, saw what crosses the boundary in each
direction, and ran CoCo itself in a sandbox that can reach only your Snowflake account.

### What You Learned
- How the plugin routes shell commands into an OpenShell sandbox
- How to remove every other shell for a team
- How to keep your token out of a sandbox with an OpenShell provider

### Related Resources
- [sandboxed-shell plugin](https://github.com/Snowflake-Labs/coco-skills/tree/main/plugins/sandboxed-shell)
- [OpenShell documentation](https://docs.nvidia.com/openshell/latest/)
- [CoCo CLI extensibility](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility)
