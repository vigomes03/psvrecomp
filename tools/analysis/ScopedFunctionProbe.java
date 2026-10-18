import java.nio.file.Paths;
import java.io.PrintWriter;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.FlowType;
import ghidra.program.model.symbol.SourceType;

/**
 * Direct Ghidra post-script for tools/analysis/scoped_function_probe.py.
 *
 * Given two explicitly bounded candidate intervals (a caller and a callee),
 * verifies the supplied call site is a direct call to the supplied callee
 * entry, then creates two USER_DEFINED functions over exactly those bounds
 * and decompiles each. Synthetic controls precede approved local R-01 analysis.
 * Private output stays in ignored lab/; not part of REA's Windows adapter.
 */
public final class ScopedFunctionProbe extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] arguments = getScriptArgs();
        if (arguments.length != 7) {
            throw new IllegalArgumentException(
                "ScopedFunctionProbe requires <imageBaseHex> <callSiteHex> <outputJsonPath> "
                + "<callerStartHex> <callerEndHex> <calleeStartHex> <calleeEndHex>"
            );
        }
        Address expectedBase = toAddr(arguments[0]);
        currentProgram.setImageBase(expectedBase, true);
        if (!currentProgram.getMinAddress().equals(expectedBase)) {
            throw new IllegalStateException("Rebased memory does not start at requested base");
        }
        String callSiteHex = arguments[1];
        String outputPath = arguments[2];
        String callerStartHex = arguments[3];
        String callerEndHex = arguments[4];
        String calleeStartHex = arguments[5];
        String calleeEndHex = arguments[6];

        String json;
        try {
            json = classify(callSiteHex, outputPath, callerStartHex, callerEndHex,
                             calleeStartHex, calleeEndHex);
        } catch (Exception error) {
            json = "{\"error\":\"" + escape(error.toString()) + "\"}";
        }

        try (PrintWriter writer = new PrintWriter(Paths.get(outputPath).toFile(), "UTF-8")) {
            writer.print(json);
        }
    }

    private String classify(String callSiteHex, String outputPath, String callerStartHex,
                             String callerEndHex, String calleeStartHex, String calleeEndHex)
            throws Exception {
        Address imageBase = currentProgram.getImageBase();
        Address callSite = toAddr(callSiteHex);
        Address callerStart = toAddr(callerStartHex);
        Address callerEnd = toAddr(callerEndHex);
        Address calleeStart = toAddr(calleeStartHex);
        Address calleeEnd = toAddr(calleeEndHex);
        String languageId = currentProgram.getLanguageID().getIdAsString();

        AddressSet callerSet = new AddressSet(callerStart, callerEnd);
        AddressSet calleeSet = new AddressSet(calleeStart, calleeEnd);
        AddressSet restrictedSet = new AddressSet(callerSet);
        restrictedSet.add(calleeSet);

        // -noanalysis leaves the image undisassembled; decode only the
        // supplied intervals, never following flow outside their union.
        DisassembleCommand callerDisasm = new DisassembleCommand(callerStart, restrictedSet, true);
        callerDisasm.applyTo(currentProgram, monitor);
        DisassembleCommand calleeDisasm = new DisassembleCommand(calleeStart, restrictedSet, true);
        calleeDisasm.applyTo(currentProgram, monitor);

        // A supplied candidate entry need not expose every observed block through
        // static flow (e.g. unresolved indirect flow). Seed the recorded site only;
        // this does NOT establish reachability from the supplied entry.
        boolean entryDecodedSite = getInstructionAt(callSite) != null;
        AddressSet siteOnly = new AddressSet(callSite, callSite.add(3));
        DisassembleCommand siteDisasm = new DisassembleCommand(callSite, siteOnly, false);
        siteDisasm.applyTo(currentProgram, monitor);
        long instructionCount = currentProgram.getListing().getNumInstructions();

        Instruction instruction = getInstructionAt(callSite);
        if (instruction == null) {
            throw new IllegalStateException("Call site did not decode to an instruction");
        }
        FlowType flowType = instruction.getFlowType();
        boolean isCall = flowType.isCall();
        if (!isCall) {
            throw new IllegalStateException("Call site is not a call instruction");
        }
        Address[] flows = instruction.getFlows();
        if (flows.length != 1) {
            throw new IllegalStateException("expected exactly one call target, found " + flows.length);
        }
        Address target = flows[0];
        if (!target.equals(calleeStart)) {
            throw new IllegalStateException(
                "Call target " + hex(target) + " does not match supplied callee entry " + hex(calleeStart)
            );
        }

        Function callerFunction = currentProgram.getFunctionManager()
            .createFunction("candidate_caller", callerStart, callerSet, SourceType.USER_DEFINED);
        Function calleeFunction = currentProgram.getFunctionManager()
            .createFunction("candidate_callee", calleeStart, calleeSet, SourceType.USER_DEFINED);

        java.nio.file.Path parent = Paths.get(outputPath).toAbsolutePath().getParent();
        java.nio.file.Path callerPseudocodePath = parent.resolve("caller.c");
        java.nio.file.Path calleePseudocodePath = parent.resolve("callee.c");

        DecompInterface decompiler = new DecompInterface();
        boolean callerDecompiled = false;
        boolean calleeDecompiled = false;
        try {
            if (!decompiler.openProgram(currentProgram)) {
                throw new IllegalStateException("Could not initialize the local decompiler");
            }
            DecompileResults callerResults = decompiler.decompileFunction(callerFunction, 10, monitor);
            if (callerResults.decompileCompleted() && callerResults.getDecompiledFunction() != null) {
                writeFile(callerPseudocodePath, callerResults.getDecompiledFunction().getC());
                callerDecompiled = true;
            } else {
                throw new IllegalStateException(
                    "Caller decompilation failed: " + callerResults.getErrorMessage()
                );
            }
            DecompileResults calleeResults = decompiler.decompileFunction(calleeFunction, 10, monitor);
            if (calleeResults.decompileCompleted() && calleeResults.getDecompiledFunction() != null) {
                writeFile(calleePseudocodePath, calleeResults.getDecompiledFunction().getC());
                calleeDecompiled = true;
            } else {
                throw new IllegalStateException(
                    "Callee decompilation failed: " + calleeResults.getErrorMessage()
                );
            }
        } finally {
            decompiler.dispose();
        }

        StringBuilder json = new StringBuilder();
        json.append('{');
        json.append("\"language\":\"").append(escape(languageId)).append("\",");
        json.append("\"image_base\":\"").append(hex(imageBase)).append("\",");
        json.append("\"call_site\":\"").append(hex(callSite)).append("\",");
        json.append("\"instruction_present\":true,");
        json.append("\"mnemonic\":\"").append(escape(instruction.getMnemonicString())).append("\",");
        json.append("\"is_call\":true,");
        json.append("\"target\":\"").append(hex(target)).append("\",");
        json.append("\"target_function\":\"").append(escape(calleeFunction.getName())).append("\",");
        json.append("\"function_count\":")
            .append(currentProgram.getFunctionManager().getFunctionCount()).append(',');
        json.append("\"function_provenance\":\"supplied-symbol-intervals\",");
        json.append("\"auto_analysis_disabled\":true,");
        json.append("\"entry_cfg_decoded_call_site\":").append(entryDecodedSite).append(',');
        json.append("\"call_site_explicitly_seeded\":true,");
        json.append("\"caller_decompiled\":").append(callerDecompiled).append(',');
        json.append("\"callee_decompiled\":").append(calleeDecompiled).append(',');
        json.append("\"caller_pseudocode\":\"")
            .append(escape(callerPseudocodePath.toString())).append("\",");
        json.append("\"callee_pseudocode\":\"")
            .append(escape(calleePseudocodePath.toString())).append("\",");
        json.append("\"caller_start\":\"").append(hex(callerStart)).append("\",");
        json.append("\"caller_end\":\"").append(hex(callerEnd)).append("\",");
        json.append("\"callee_start\":\"").append(hex(calleeStart)).append("\",");
        json.append("\"callee_end\":\"").append(hex(calleeEnd)).append("\",");
        json.append("\"decoded_instruction_count\":").append(instructionCount);
        json.append('}');
        return json.toString();
    }

    private static void writeFile(java.nio.file.Path path, String content) throws Exception {
        try (PrintWriter writer = new PrintWriter(path.toFile(), "UTF-8")) {
            writer.print(content);
        }
    }

    private static String hex(Address address) {
        return "0x" + Long.toHexString(address.getOffset());
    }

    private static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
