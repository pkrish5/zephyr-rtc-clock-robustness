# S1 subject survey, 2026-10-25

Read-only survey only. No builds, Renode runs, jobs or model generations were performed. E job 3532543 was untouched; E2 and paper edits remain held. Stop here for S2 subject/board approval.

## Pins and limits

Zephyr commit: `3568e1b6d5cdd51a6b964a2a1d6d29200fea2056`. Renode calibrated release source: `f1dd1b4af7838b45a925c17603cdfed0a583844a`; infrastructure submodule: `cd4b002aac2398994c4a61a34a8b31b5700facf2`. The model-source URLs and hashes are in `renode_model_sources.json`. S1 registration is the 2026-10-25 amendment in `paper/DESIGN.md`.

Build status is verified only where existing frozen records/configurations provide evidence. All new-board and new-config build/run claims remain unverified. Static model presence is insufficient for corpus admission.

## Every case, including exclusions

`test_cases.csv` has 68 rows: 45 ztest declarations plus one console behavior in the requested applications, and 22 declarations in adjacent hardware-free/vendor-specific applications kept as explicit exclusions. The prospective non-watchdog cohort has 19 distinct declarations across three applications, not 19 independent programs. Conditional compilation, capability skips, build losses, nominal failures and harness errors must remain separate.

| Application | Declarations | STM32F4 evidence and disposition |
|---|---:|---|
| rtc/rtc_api |7| Existing full-app build covers 5 cases. Update and calibration were not enabled. Y2K is expected to skip because pre-2000 years are rejected; update callback is expected to skip because the STM32 API lacks that operation. Calibration fields are tagged in the model and do not establish oscillator-correction fidelity. |
| counter/counter_basic_api |11| Source supports STM32 RTC. Stock F4 overlay instead enables timer counters and disables RTC. A new RTC-only config is required; 1 Hz and optional subsecond variants repeat the same cases. Capability skips are expected but not measured. |
| counter/counter_seconds |1| Source uses rtc_0 alias outside CMOS; stock YAML only selects x86/NXP. A new alias/config could target the STM32 RTC counter; no C changes or builds performed. |
| watchdog/wdt_basic_api |1| Existing configured build succeeds, but the prior five fidelity probes never demonstrate reboot and case completion. Exclude from production until independently qualified. |
| watchdog/wdt_basic_reset_none |2| Stock filter is not STM32; reset-none/callback capabilities do not match STM32 IWDG. |
| watchdog/wdt_error_cases |23| Stock platform list excludes STM32 and several required capabilities are unavailable. Inventory is exhaustive, not a claim of 23 runnable STM32 subjects. |
| watchdog/wdt_variables |0 ztests; 1 console behavior| Nordic-only platform list. Not an additional STM32 case. |

The CSV records each case name, exact source span, build evidence, model status, source-reachable timing cues, configuration gate and caveats. Wait cues include callbacks/function-pointer helpers and fixtures; they are not a proof that every cue is an unjustified bound.

### Prospective case names

- **rtc_api**: `rtc_api.test_alarm`, `rtc_api.test_alarm_callback`, `rtc_api.test_set_get_calibration`, `rtc_api.test_set_get_time`, `rtc_api.test_time_counting`, `rtc_api.test_update_callback`, `rtc_api.test_y2k`.
- **counter_basic_api**: `counter_basic.test_set_top_value_with_alarm`, `counter_no_callback.test_set_top_value_without_alarm`, `counter_basic.test_single_shot_alarm_notop`, `counter_basic.test_single_shot_alarm_top`, `counter_basic.test_multiple_alarms`, `counter_basic.test_all_channels`, `counter_basic.test_valid_function_without_alarm`, `counter_basic.test_late_alarm`, `counter_basic.test_late_alarm_error`, `counter_basic.test_short_relative_alarm`, `counter_basic.test_cancelled_alarm_does_not_expire`.
- **counter_seconds**: `seconds_counter.test_seconds_rate`.

## Board survey

All 233 STM32 DTS targets resolved, across 210 board directories. `stm32_board_targets.csv` is the final full list; diagnostic passes are superseded. The survey preprocesses the include tree and resolves labels/phandles, distinguishes APB gate clocks from source selectors and honors peripheral/ancestor status. No application overlays or firmware configuration builds are applied. The only independent board.yml cross-check omission is the Nordic coprocessor target of 96Boards Carbon, which is not an STM32 target.

| Default board DTS state | Targets |
|---|---:|
| RTC enabled with LSI selection |106|
| RTC enabled with LSE selection |40|
| RTC enabled, source not selected/resolved |4|
| RTC disabled or absent |83|
| Total |233|

The four enabled-but-unselected cases are Arduino Opta/Portenta H7 M4/M7 targets. Their DTS has an APB gate clock but no RTC source specifier; no LSI/LSE choice was inferred. LSI RTC targets span 104 board directories; LSE targets span 35, with variants counted separately above. This is repository-configuration prevalence, not deployed-board or physical-frequency prevalence.

IWDG is DT-enabled on 101 targets (96 board directories). 55 of those also enable the LSI clock node; 46 do not. This does not mean 46 watchdogs lack a clock: the STM32 driver and hardware force LSI on when IWDG starts. The overlap cannot establish that LSI was enabled exclusively for IWDG rather than RTC or another peripheral.

## Boards and verified oscillator bounds

| Board | Default RTC | LSI kHz | Renode RTC / IWDG | Status |
|---|---|---|---|---|
|stm32f4_disco|LSI|17–47|STM32F4_RTC / present; prior fidelity failure|existing calibration for selected RTC cases only; expanded applications/configurations unverified|
|nucleo_f767zi|LSI|17–47|STM32F4_RTC / absent|priority candidate; existing Zephyr DTS and Renode board; build and timing calibration not run|
|stm32f746g_disco|LSI|17–47|STM32F4_RTC / absent|priority candidate; build, console/platform matching and timing calibration not run|
|nucleo_h753zi|LSI|29.76–33.6|STM32F4_RTC / present; not reset-qualified|priority narrower-range candidate; silicon revision and temperature envelope must be frozen before S2|
|stm32h747i_disco/stm32h747xx/m7|disabled|29.76–33.6|STM32F4_RTC / present; not reset-qualified|conditional; needs approved LSI/RTC overlay, single-core boot/console and peripheral qualification|
|stm32f072b_disco|disabled|30–50|STM32F4_RTC / absent|conditional; needs approved RTC/LSI overlay and explicit divider policy for 40-kHz nominal oscillator; do not transplant F4 thresholds|

The priority new-board candidates are F767ZI, F746G Discovery and H753ZI. H753 changes the clock-range stratum; F767/F746 retain the wider 17–47-kHz range. These share the STM32 RTC driver family and often the same Renode RTC model, so they do not provide an independent simulator or a different-vendor replication. All need nominal and endpoint/reference qualification before production.

H747 requires RTC/LSI enablement and core/boot qualification. F072 requires an explicit 40-kHz divider policy: the RTC driver defaults to 128×250 for an LSI source, so the F4 equation cannot simply be transplanted. Both are conditional proposals.

Additional model-presence findings: `nucleo_wba52cg.repl` has no matching board definition in this Zephyr pin (WBA55 is a different target); `ramn.repl` also lacks a matching pinned board. RAMN uses STM32L_RTC, whose source supplies a 1000-Hz guessed wakeup timer rather than a qualified calendar model. Do not admit them as ready-to-run boards. Their entries remain in `renode_platform_inventory.csv`.

## Costed proposal, not submitted work

Minimal option per approved board: three full applications, 5 nominal launches plus 100 settings and two endpoints each = 321 firmware launches, with 1,938 scheduled case-verdict slots before skips and 95 nominal case slots. Optional subsecond counter adds 107 launches, repeating 11 cases: 428 launches total, 3,060 scheduled case/config slots. Neither option launches one Slurm task per case; each Launcher line executes one full application/configuration at one frequency.

Planning costs use 32 workers, assumed full-launch wall caps of 180 s for RTC, 600 s for generic counter and 60 s for seconds-rate; optional subsecond counter adds another 600 s. Nominal/primary ideal totals are 0.78 SU or 1.34 SU per board. After 30% overhead, qualification minimum and a provisional replay/reference reserve, budget approximately 2 SU (minimal) or 3 SU (with subsecond) per board. These are unmeasured new-app estimates; the contingent replay/reference workload is not known. Recost and report exact node/wall/SU requests before any normal submission. New-app RSS must keep concurrency below 80% of node memory.

For existing F4 plus the three priority new boards: 1,284 primary launches and 7,752 scheduled case slots, about 8 SU under the minimal planning budget; optional subsecond configs give 1,712 launches and 12,240 scheduled case/config slots, about 12 SU. No S2 job is submitted or approved by S1. Missing, skipped and failed nominal outcomes must not be forced into timing-flip denominators.

## ST documentation and distribution evidence

- **AN5067: How to optimize STM32 MCUs internal RC oscillator accuracy** (Rev 1, March 2018). Introduction and sections 2/3 discuss assembly, thermal and mechanical effects. Figure 1 measures HSI16 on 500 STM32F767 boards, not LSI. Does not supply a usable F407 LSI population distribution. [ST source](https://www.st.com/resource/en/application_note/dm00425536-how-to-optimize-stm32-mcus-internal-rc-oscillator-accuracy-stmicroelectronics.pdf).
- **AN5126: How to calibrate internal oscillators on STM32G0 MCUs** (Rev 2, April 2023). Sections 2/3/4 distinguish HSI trimming from LSI measurement, discuss process/temperature/voltage effects and timer capture. LSI is measured, not directly trimmed, on this family. No population probability model identified. [ST source](https://www.st.com/resource/en/application_note/dm00469014-using-xcuberccalib-software-to-calibrate-stm32g0-series-internal-rc-oscillator-stmicroelectronics.pdf).
- **RM0090: STM32F405/415, STM32F407/417, STM32F427/437 and STM32F429/439 advanced Arm-based 32-bit MCUs** (Indexed Rev 21 clock-measurement section 6.2.11, pp. 160-161; current ST index advertises Rev 22 separately). Verified ST-hosted indexed passage describes manufacturing deviation and TIM5 channel 4 LSI measurement, then adjusting RTC prescaler/IWDG timeout. Full local PDF retrieval failed; do not claim an archived PDF or full-manual distribution search. [ST source](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f10x-microcontrollers-stmicroelectronics.pdf).
- **DS8626: STM32F405xx STM32F407xx datasheet** (Rev 12, Table 35 and Figure 34). 17/32/47-kHz characterization limits plus min/average/max temperature curves. These are not a device-frequency probability distribution. [ST source](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf).

No F407 LSI population distribution was identified in the reviewed sources. ST documents manufacturing and environmental variability and measurement/compensation techniques. Datasheet envelopes and temperature curves do not justify treating uniform sampling as a measured share of devices. AN5067 does show a 500-device HSI example; it is not an LSI distribution. Any normal distributions in S3 must remain explicitly illustrative. Full local ST PDF download attempts failed (TLS/transport); the titles/passages/tables above were verified through ST-hosted indexed PDF content. Do not claim locally archived ST PDFs.

## Stop

S1 is complete only as a survey. Approve subjects, board/configuration choices and qualification scope before S2; no distribution calculations, coverage runs, new generation specifications or model calls have been executed. E remains untouched and E2 remains held.


## Model evidence and comparability limits

- The exact-release `STM32F4_RTC.cs` models calendar/alarm and subsecond behavior, but its calibration registers at lines 309–313 and 451–457 contain tagged fields. The source does not establish calibrated-rate fidelity. The STM32 driver's API table omits update callbacks, and its pre-2000 check explains the two expected skips.
- `STM32_IndependentWatchdog.cs` implements `machine.RequestReset()` and explicitly leaves RCC reset-cause handling as a TODO (lines 20–21, 137–140). This supports model presence, not a demonstrated reboot path. The existing F4 probe's absent reboot remains unexplained; do not claim this TODO is its proven cause.
- RAMN's `STM32L_RTC.cs` constructor uses a guessed 1000-Hz wakeup timer. This is not evidence of a faithful low-speed calendar RTC.
- Adding cases/boards improves baseline coverage but does not remove the initial task-specification precision confound. Shared driver/model code and repeated board targets remain clustered observations. Driver coverage and matched-purpose/augmentation comparisons belong to later approved phases; S1 does not claim generated/developer equivalence.

No manuscript or frozen experimental number was changed. The only numeric additions are this source survey and explicitly hypothetical workload estimates.

### Board revision overlay check

Board revision metadata and board-owned overlays were also checked. Only two overlays affect the surveyed clocks: Portenta H7 M7 revision 1.0.0 enables `clk_lsi`, while revision 4.10.0 enables `clk_lse`. Neither supplies a missing RTC source selector or changes IWDG enablement. Thus the reported RTC-source and IWDG counts describe the base DTS targets; revision clock-enable differences are disclosed in `board_overlays.csv` rather than silently counted as additional boards. General LSI-clock-node enablement counts are specifically base-DTS counts.
