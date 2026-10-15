// EXCERPT of Eden (GPLv3, read-only reference, do NOT copy code) eden-master/eden/src/core/hle/kernel/k_condition_variable.cpp lines 240-345:
// KConditionVariable::Signal and ::Wait = the real Horizon semantics (mesosphere-equivalent).
        // If the address wasn't accessible, note so.
        thread->EndWait(kernel, ResultInvalidCurrentMemory);
    }
}

void KConditionVariable::Signal(u64 cv_key, s32 count) {
    // Perform signaling.
    s32 num_waiters{};
    {
        KScopedSchedulerLock sl(m_system.Kernel());

        auto it = m_tree.nfind_key({cv_key, -1});
        while ((it != m_tree.end()) && (count <= 0 || num_waiters < count) && (it->GetConditionVariableKey() == cv_key)) {
            KThread* target_thread = std::addressof(*it);

            it = m_tree.erase(it);
            target_thread->ClearConditionVariable();

            this->SignalImpl(m_system.Kernel(), target_thread);

            ++num_waiters;
        }

        // If we have no waiters, clear the has waiter flag.
        if (it == m_tree.end() || it->GetConditionVariableKey() != cv_key) {
            constexpr u32 HasNoWaiterFlag = 0;
            WriteToUser(m_system.Kernel(), cv_key, HasNoWaiterFlag);
        }
    }
}

Result KConditionVariable::Wait(KProcessAddress addr, u64 key, u32 value, s64 timeout) {
    // Prepare to wait.
    KThread* cur_thread = GetCurrentThreadPointer(m_system.Kernel());
    KHardwareTimer* timer{};
    ThreadQueueImplForKConditionVariableWaitConditionVariable wait_queue(m_system.Kernel(),
                                                                         std::addressof(m_tree));

    {
        KScopedSchedulerLockAndSleep slp(m_system.Kernel(), std::addressof(timer), cur_thread, timeout);

        // Check that the thread isn't terminating.
        if (cur_thread->IsTerminationRequested()) {
            slp.CancelSleep();
            R_THROW(ResultTerminationRequested);
        }

        // Update the value and process for the next owner.
        {
            // Remove waiter thread.
            bool has_waiters{};
            KThread* next_owner_thread =
                cur_thread->RemoveUserWaiterByKey(m_system.Kernel(), std::addressof(has_waiters), addr);

            // Update for the next owner thread.
            u32 next_value{};
            if (next_owner_thread != nullptr) {
                // Get the next tag value.
                next_value = next_owner_thread->GetAddressKeyValue();
                if (has_waiters) {
                    next_value |= Svc::HandleWaitMask;
                }

                // Wake up the next owner.
                next_owner_thread->EndWait(m_system.Kernel(), ResultSuccess);
            }

            // Write to the cv key.
            {
                constexpr u32 HasWaiterFlag = 1;
                WriteToUser(m_system.Kernel(), key, HasWaiterFlag);
                std::atomic_thread_fence(std::memory_order_seq_cst);
            }

            // Write the value to userspace.
            if (!WriteToUser(m_system.Kernel(), addr, next_value)) {
                slp.CancelSleep();
                R_THROW(ResultInvalidCurrentMemory);
            }
        }

        // If timeout is zero, time out.
        R_UNLESS(timeout != 0, ResultTimedOut);

        // Update condition variable tracking.
        cur_thread->SetConditionVariable(std::addressof(m_tree), addr, key, value);
        m_tree.insert(*cur_thread);

        // Begin waiting.
        wait_queue.SetHardwareTimer(timer);
        cur_thread->BeginWait(m_system.Kernel(), std::addressof(wait_queue));
        cur_thread->SetWaitReasonForDebugging(ThreadWaitReasonForDebugging::ConditionVar);
    }

    // Get the wait result.
    R_RETURN(cur_thread->GetWaitResult());
}

} // namespace Kernel
