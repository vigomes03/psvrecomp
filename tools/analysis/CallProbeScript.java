import java.nio.file.Paths;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.FlowType;

/**
 * Direct Ghidra post-script for tools/analysis/ghidra_call_probe.py.
 *
 * Classifies one caller-supplied address in the current program as a call
 * instruction or not, and reports the resolved target function if it is.
 * Used only against our own synthetic AArch64 fixtures (tools/analysis);
 * this is not part of REA's Windows raw-binary admission path.
 */
public final class CallProbeScript extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] arguments = getScriptArgs();
        if (arguments.length != 3) {
            throw new IllegalArgumentException(
                "CallProbeScript requires <imageBaseHex> <callSiteHex> <outputJsonPath>"
            );
        }
        // BinaryLoader places its block at loader-baseAddr but creates a program
        // with image base zero. Import at zero and genuinely rebase the program
        // before decoding, rather than relabeling the returned metadata.
        Address expectedBase = toAddr(arguments[0]);
        currentProgram.setImageBase(expectedBase, true);
        if (!currentProgram.getMinAddress().equals(expectedBase)) {
            throw new IllegalStateException("Rebased memory does not start at requested base");
        }
        String callSiteHex = arguments[1];
        String outputPath = arguments[2];

        String json;
        try {
            json = classify(callSiteHex);
        } catch (Exception error) {
            json = "{\"error\":\"" + escape(error.toString()) + "\"}";
        }

        try (PrintWriter writer = new PrintWriter(Paths.get(outputPath).toFile(), "UTF-8")) {
            writer.print(json);
        }
    }

    private String classify(String callSiteHex) throws Exception {
        Address imageBase = currentProgram.getImageBase();
        Address callSite = currentProgram.getAddressFactory()
            .getDefaultAddressSpace().getAddress(callSiteHex);
        String languageId = currentProgram.getLanguageID().getIdAsString();

        // -noanalysis leaves the image undisassembled; decode only the
        // requested address on demand, bounded to this one probe query.
        Instruction instruction = getInstructionAt(callSite);
        if (instruction == null) {
            disassemble(callSite);
            instruction = getInstructionAt(callSite);
        }

        StringBuilder json = new StringBuilder();
        json.append('{');
        json.append("\"language\":\"").append(escape(languageId)).append("\",");
        json.append("\"image_base\":\"").append(hex(imageBase)).append("\",");
        json.append("\"call_site\":\"").append(hex(callSite)).append("\",");

        if (instruction == null) {
            json.append("\"instruction_present\":false,\"is_call\":false,");
            json.append("\"mnemonic\":null,\"target\":null,\"target_function\":null");
        } else {
            FlowType flowType = instruction.getFlowType();
            boolean isCall = flowType.isCall();
            json.append("\"instruction_present\":true,");
            json.append("\"mnemonic\":\"").append(escape(instruction.getMnemonicString())).append("\",");
            json.append("\"is_call\":").append(isCall).append(',');
            if (isCall) {
                Address[] flows = instruction.getFlows();
                if (flows.length != 1) {
                    throw new IllegalStateException(
                        "expected exactly one call target, found " + flows.length
                    );
                }
                Address target = flows[0];
                Function function = getFunctionAt(target);
                if (function == null) {
                    disassemble(target);
                    function = createFunction(target, null);
                }
                json.append("\"target\":\"").append(hex(target)).append("\",");
                json.append("\"target_function\":")
                    .append(function == null ? "null" : "\"" + escape(function.getName()) + "\"");
            } else {
                json.append("\"target\":null,\"target_function\":null");
            }
        }
        json.append('}');
        return json.toString();
    }

    private static String hex(Address address) {
        return "0x" + Long.toHexString(address.getOffset());
    }

    private static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
