### Fixed

- Fixed issue #2615. The portal refuses a firmware write when the operator address uses a reserved domain such as `.invalid`, because that address reaches no mailbox and no person can answer for the write. The refusal covers the single-site start and the multi-site start. A capture and every read still accept any address. The run page and the history page now show the Mist account beside the typed address.
