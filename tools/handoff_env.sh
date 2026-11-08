#!/usr/bin/env bash
# Source this file; no login data or activation is performed.
task_handoff_project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
task_handoff_tools="${AC_TOOLCHAIN_ROOT:-$(dirname "$task_handoff_project")/toolchains}"
if [[ -x "$task_handoff_tools/mono-unity-6000.3.27f2/bin-linux64/mono" ]]; then
    export UNITY_MONO_ROOT="$task_handoff_tools/mono-unity-6000.3.27f2"
fi
if [[ -d "$task_handoff_tools/jdk-25.0.5+8" ]]; then
    export JAVA_HOME="$task_handoff_tools/jdk-25.0.5+8"
fi
export AC_PROJECT_ROOT="$task_handoff_project"
export AC_TOOLCHAIN_ROOT="$task_handoff_tools"
export PATH="$task_handoff_project/.venv/bin:$PATH"
unset task_handoff_project task_handoff_tools
