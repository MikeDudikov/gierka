#!/usr/bin/env bash
# Static local analysis only; never executes the original program.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
toolchain_root="${ANCIENT_TOOLCHAIN_ROOT:-$(dirname -- "$repo_root")/toolchains}"
ghidra_root="$toolchain_root/ghidra_12.2_PUBLIC"
jdk_root="$toolchain_root/jdk-25.0.5+8"
analysis_root="$repo_root/artifacts/binary-analysis"
report_root="${1:-$analysis_root/export}"
[[ -x "$ghidra_root/support/analyzeHeadless" && -x "$jdk_root/bin/java" ]]
if [[ -e "$report_root" ]]; then
  echo "Report destination already exists: $report_root" >&2
  exit 1
fi
mkdir -p "$analysis_root/input" "$analysis_root/projects" "$toolchain_root/ghidra-config" "$toolchain_root/ghidra-cache"
cd "$repo_root"
.venv/bin/python - <<'PYTHON'
from pathlib import Path
import hashlib, json, pefile, re, shutil
root=Path('artifacts/binary-analysis')
source=Path('reference/raw/ancient-conquest/installed/ancient.exe')
expected='cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021'
raw=source.read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected: raise SystemExit('Unexpected original executable')
copy=root/'input/ancient.exe'
if copy.exists():
 if hashlib.sha256(copy.read_bytes()).hexdigest()!=expected: raise SystemExit('Different copied executable')
else: shutil.copyfile(source,copy)
pe=pefile.PE(data=raw)
rows=[]
for m in re.finditer(rb'[\x20-\x7e]{6,}',raw):
 text=m.group().decode('ascii'); low=text.lower()
 if any(t in low for t in ('\\ai\\','\\brain\\miss','\\artem\\l_ai','\\artem\\_l_ai','kib','timer','clock','timeclass','tik ','ancientappty::startgame','gamesystemty::','basesystemty::','plrbasesystemty::','gamesys.cpp')):
  try: address=pe.OPTIONAL_HEADER.ImageBase+pe.get_rva_from_offset(m.start())
  except pefile.PEFormatError: continue
  rows.append(dict(va=f'{address:x}',offset=m.start(),text=text))
(root/'candidate-strings.json').write_text(json.dumps(rows,indent=2)+'\n')
(root/'candidate-strings.tsv').write_text(''.join(f"{r['va']}\t{r['text']}\n" for r in rows))
PYTHON
cat > "$analysis_root/ExportEvidence.java" <<'JAVA'
// Local analysis of the supplied original. Does not execute or modify game code.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import java.nio.file.*;
import java.io.*;
import java.util.*;

public class ExportEvidence extends GhidraScript {
    private String q(String s) {
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"")
            .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + "\"";
    }
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Path output = Paths.get(args[0]);
        Files.createDirectories(output.resolve("decompiled"));
        LinkedHashMap<Function, List<String>> selected = new LinkedHashMap<>();
        List<String> refs = new ArrayList<>();
        String[][] timers = {
            {"5942d4", "timeSetEvent"}, {"5942d8", "timeGetTime"},
            {"5942dc", "timeKillEvent"}, {"5942f4", "timeBeginPeriod"},
            {"594148", "GetTickCount"}, {"594158", "Sleep"}
        };
        for (String[] timer : timers) {
            Address address = toAddr(timer[0]);
            for (Reference ref : getReferencesTo(address)) {
                Function fn = getFunctionContaining(ref.getFromAddress());
                refs.add("{\"kind\":\"timer_import\",\"label\":" + q(timer[1]) +
                    ",\"target\":" + q(address.toString()) + ",\"from\":" + q(ref.getFromAddress().toString()) +
                    ",\"function\":" + q(fn == null ? "" : fn.getEntryPoint().toString()) + "}");
                if (fn != null) selected.computeIfAbsent(fn, k -> new ArrayList<>()).add(timer[1]);
            }
        }
        for (String line : Files.readAllLines(Paths.get(args[1]))) {
            String[] fields = line.split("\t", 2);
            if (fields.length != 2) continue;
            Address address = toAddr(fields[0]);
            for (Reference ref : getReferencesTo(address)) {
                Function fn = getFunctionContaining(ref.getFromAddress());
                refs.add("{\"kind\":\"diagnostic_string\",\"label\":" + q(fields[1]) +
                    ",\"target\":" + q(address.toString()) + ",\"from\":" + q(ref.getFromAddress().toString()) +
                    ",\"function\":" + q(fn == null ? "" : fn.getEntryPoint().toString()) + "}");
                if (fn != null) selected.computeIfAbsent(fn, k -> new ArrayList<>()).add(fields[1]);
            }
        }
        // Include direct callers of timer wrapper and named AI candidates.
        List<Function> seeds = new ArrayList<>(selected.keySet());
        for (Function fn : seeds) {
            List<String> why = selected.get(fn);
            boolean includeCallers = why.stream().anyMatch(v -> v.equals("timeSetEvent") || v.contains("Boss_Kib") || v.contains("L_Ai.cpp"));
            if (!includeCallers) continue;
            for (Reference ref : getReferencesTo(fn.getEntryPoint())) {
                Function caller = getFunctionContaining(ref.getFromAddress());
                if (caller != null && ref.getReferenceType().isCall())
                    selected.computeIfAbsent(caller, k -> new ArrayList<>()).add("calls " + fn.getEntryPoint());
            }
        }
        String[][] exactSeeds = {{"5417d0", "clock read used by GameSystemTy::Life"},
            {"541520", "application iteration dispatch called by RunApp"},
            {"5413c0", "LifeToAllSystem call from application iteration"},
            {"448610", "Boss_Kib decision callee from GetMessage"},
            {"4ed41b", "SPEED_GAME configuration xref"},
            {"5118d8", "SPEED_GAME UI/configuration xref"},
            {"4ef570", "AncientAppTy::CommonFunction cadence path"},
            {"501739", "configuration initializes speed index to five"},
            {"520352", "PlaySystemClassTy::Life time-quantum branch"},
            {"521d67", "world-step speed table parameter use"},
            {"50f858", "GameSystemTy::Life diagnostic xref"},
            {"52e38e", "PlrBaseSystemTy::Life diagnostic xref"},
            {"448de7", "Boss_KibClassTy::GetMessage diagnostic xref"}};
        for (String[] seed : exactSeeds) {
            Function fn = getFunctionContaining(toAddr(seed[0]));
            if (fn != null) selected.computeIfAbsent(fn, k -> new ArrayList<>()).add(seed[1]);
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        List<String> functions = new ArrayList<>();
        int count = 0;
        for (Map.Entry<Function,List<String>> entry : selected.entrySet()) {
            if (count++ >= 250) break;
            Function fn = entry.getKey();
            String filename = fn.getEntryPoint().toString() + ".c";
            DecompileResults result = decompiler.decompileFunction(fn, 45, monitor);
            boolean success = result.decompileCompleted() && result.getDecompiledFunction() != null;
            if (success) Files.writeString(output.resolve("decompiled").resolve(filename), result.getDecompiledFunction().getC());
            List<String> calls = new ArrayList<>();
            for (Function called : fn.getCalledFunctions(monitor)) calls.add(q(called.getEntryPoint() + ":" + called.getName()));
            List<String> reasons = new ArrayList<>();
            for (String why : entry.getValue()) reasons.add(q(why));
            functions.add("{\"address\":" + q(fn.getEntryPoint().toString()) + ",\"name\":" + q(fn.getName()) +
                ",\"size\":" + fn.getBody().getNumAddresses() + ",\"decompiled\":" + success +
                ",\"file\":" + q(success ? "decompiled/" + filename : "") + ",\"reasons\":[" + String.join(",", reasons) +
                "],\"calls\":[" + String.join(",", calls) + "]}");
        }
        decompiler.dispose();
        Files.writeString(output.resolve("evidence.json"), "{\"program\":" + q(currentProgram.getName()) +
            ",\"program_sha256\":" + q(currentProgram.getExecutableSHA256()) +
            ",\"image_base\":" + q(currentProgram.getImageBase().toString()) + ",\"function_count\":" +
            currentProgram.getFunctionManager().getFunctionCount() + ",\"references\":[" + String.join(",", refs) +
            "],\"functions\":[" + String.join(",", functions) + "]}\n");
        println("Exported " + functions.size() + " functions and " + refs.size() + " references");
    }
}
JAVA
export XDG_CONFIG_HOME="$toolchain_root/ghidra-config"
export XDG_CACHE_HOME="$toolchain_root/ghidra-cache"
export JAVA_HOME="$jdk_root"
export GHIDRA_HEADLESS_MAXMEM=8G
if [[ -f "$analysis_root/projects/AncientConquest.gpr" ]]; then
  project_args=(-process ancient.exe -readOnly -noanalysis)
else
  project_args=(-import "$analysis_root/input/ancient.exe" -analysisTimeoutPerFile 180)
fi
"$ghidra_root/support/analyzeHeadless" "$analysis_root/projects" AncientConquest   "${project_args[@]}" -max-cpu 4 -scriptPath "$analysis_root"   -postScript ExportEvidence.java "$report_root" "$analysis_root/candidate-strings.tsv"   -log "$report_root.log"
.venv/bin/python - "$report_root/evidence.json" <<'PYTHON'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
assert r['program_sha256']=='cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021'
assert r['functions'] and r['references']
print('Static export verified:',len(r['functions']),'functions;',len(r['references']),'references')
PYTHON
