// Native Windows SEH fault context diagnostic (verification infrastructure, see
// tools/verify/test_windows_fault_context.py). Prints raw EXCEPTION_RECORD/CONTEXT
// fields before any existing terminal reporter runs, so a real crash's register
// state is not lost if later reporting code itself faults.
#ifndef PVR_WINDOWS_FAULT_CONTEXT_H
#define PVR_WINDOWS_FAULT_CONTEXT_H

#include <windows.h>
#include <stdio.h>

// Access classification per EXCEPTION_RECORD docs (winnt.h):
// https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-exception_record
// ExceptionInformation[0] is only meaningful for EXCEPTION_ACCESS_VIOLATION or
// EXCEPTION_IN_PAGE_ERROR with at least 2 parameters: 0=read, 1=write, 8=execute.
static inline void pvr_print_windows_fault_context(FILE *stream, const EXCEPTION_RECORD *er,
                                                     const CONTEXT *ctx) {
    const char *access = "unknown";
    int valid = 0;
    unsigned long long operation = 0;
    unsigned long long address = 0;

    if ((er->ExceptionCode == EXCEPTION_ACCESS_VIOLATION || er->ExceptionCode == EXCEPTION_IN_PAGE_ERROR) &&
        er->NumberParameters >= 2) {
        operation = (unsigned long long)er->ExceptionInformation[0];
        address = (unsigned long long)er->ExceptionInformation[1];
        valid = 1;
        if (operation == 0) access = "read";
        else if (operation == 1) access = "write";
        else if (operation == 8) access = "execute";
        else { access = "unknown"; valid = 0; }
    }

    fprintf(stream, "[host-context] code=%08lx access=%s valid=%d", (unsigned long)er->ExceptionCode, access, valid);
    if (valid) fprintf(stream, " operation=%llu", operation);
    fprintf(stream, " address=%016llx flags=%08lx\n", address, (unsigned long)er->ExceptionFlags);

    fprintf(stream,
        "[host-context] rax=%016llx rbx=%016llx rcx=%016llx rdx=%016llx rsi=%016llx rdi=%016llx\n",
        (unsigned long long)ctx->Rax, (unsigned long long)ctx->Rbx, (unsigned long long)ctx->Rcx,
        (unsigned long long)ctx->Rdx, (unsigned long long)ctx->Rsi, (unsigned long long)ctx->Rdi);
    fprintf(stream,
        "[host-context] rbp=%016llx rsp=%016llx r8=%016llx r9=%016llx r10=%016llx r11=%016llx\n",
        (unsigned long long)ctx->Rbp, (unsigned long long)ctx->Rsp, (unsigned long long)ctx->R8,
        (unsigned long long)ctx->R9, (unsigned long long)ctx->R10, (unsigned long long)ctx->R11);
    fprintf(stream,
        "[host-context] r12=%016llx r13=%016llx r14=%016llx r15=%016llx rip=%016llx\n",
        (unsigned long long)ctx->R12, (unsigned long long)ctx->R13, (unsigned long long)ctx->R14,
        (unsigned long long)ctx->R15, (unsigned long long)ctx->Rip);
    fflush(stream);
}

#endif
