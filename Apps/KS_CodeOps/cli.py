import argparse
import json
import os
import sys
import tempfile
from datetime import datetime

from src.automation.factory import build_automation
from src.core.config import AppConfig
from src.core.job_runner import JobRunner
from src.core.materializer import AppMaterializer
from src.core.plan_builder import PlanBuilder
from src.core.sequencer import VSCodeSequencer
from src.version import __version__


def _safe_print(value):
    text = str(value)
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))
            sys.stdout.flush()
        else:
            print(text.encode("ascii", errors="replace").decode("ascii"))


class _SmokeSequencer:
    def _log(self, message: str):
        print(message)

    def send_text(self, _text: str, press_enter: bool, target_name=None):
        return True

    def send_image(self, _image_path: str, press_enter: bool, target_name=None):
        return True


def _run_release_smoke(config: AppConfig, keep_temp: bool = False) -> bool:
    temp_ctx = tempfile.TemporaryDirectory(prefix="ks_codeops_smoke_")
    job_dir = temp_ctx.name
    smoke_adapter_name = "__ks_smoke_adapter__"
    original_adapters = dict(getattr(config, "worker_adapters", {}) or {})

    try:
        adapter_script = os.path.join(job_dir, "smoke_adapter.py")
        with open(adapter_script, "w", encoding="utf-8") as handle:
            handle.write(
                "import json, sys\n"
                "request_path, response_path = sys.argv[1], sys.argv[2]\n"
                "with open(request_path, 'r', encoding='utf-8') as r:\n"
                "    payload = json.load(r)\n"
                "step_id = payload.get('step_id', 'smoke')\n"
                "response = {\n"
                "    'status': 'ok',\n"
                "    'output_text': '# Smoke Run\\n' + step_id + '\\n',\n"
                "    'notes_md': 'smoke notes',\n"
                "}\n"
                "with open(response_path, 'w', encoding='utf-8') as w:\n"
                "    json.dump(response, w)\n"
            )

        adapters = dict(original_adapters)
        adapters[smoke_adapter_name] = {
            "command": "\"{python}\" \"{adapter_script}\" \"{request_file}\" \"{response_file}\"",
            "command_vars": {"adapter_script": adapter_script},
            "timeout_s": 20,
            "poll_interval_s": 0.1,
        }
        config.worker_adapters = adapters

        plan = {
            "name": "release_smoke",
            "steps": [
                {
                    "id": "smoke_worker",
                    "type": "worker_contract",
                    "target": config.active_target,
                    "content": "release smoke",
                    "worker": {"adapter": smoke_adapter_name},
                    "output_file": "outputs/smoke.md",
                    "validator": {"type": "sections", "required": ["# Smoke Run"]},
                },
                {
                    "id": "smoke_validate",
                    "type": "validate",
                    "output_file": "outputs/smoke.md",
                    "validator": {"type": "exists"},
                },
            ],
        }
        with open(os.path.join(job_dir, "plan.json"), "w", encoding="utf-8") as handle:
            json.dump(plan, handle, indent=2)

        runner = JobRunner(_SmokeSequencer(), config)
        ok = runner.run_job(job_dir)
        status_path = os.path.join(job_dir, "status.json")
        if not ok or not os.path.exists(status_path):
            print(f"smoke-run: FAIL ({job_dir})")
            return False
        with open(status_path, "r", encoding="utf-8") as handle:
            status = json.load(handle)
        final_ok = bool(ok and status.get("state") == "completed")
        print(f"smoke-run: {'PASS' if final_ok else 'FAIL'} ({job_dir})")
        return final_ok
    finally:
        config.worker_adapters = original_adapters
        if keep_temp:
            print(f"smoke-run temp kept: {job_dir}")
            if hasattr(temp_ctx, "_finalizer"):
                temp_ctx._finalizer.detach()
        else:
            temp_ctx.cleanup()


def build_parser():
    parser = argparse.ArgumentParser(description="KS CodeOps CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version")

    smoke = sub.add_parser("smoke-run")
    smoke.add_argument("--keep-temp", action="store_true", help="Keep temporary smoke-run workspace")

    sub.add_parser("windows")

    focus = sub.add_parser("focus")
    focus.add_argument("--profile", choices=["editor", "chat_panel"])
    focus.add_argument("--window-title", help="Window title substring to focus")
    focus.add_argument("--maximize", action="store_true", help="Maximize focused window")
    focus.add_argument("--no-maximize", action="store_true", help="Do not maximize on focus")

    set_window = sub.add_parser("set-window-title")
    set_window.add_argument("--title", required=True)

    set_max = sub.add_parser("set-maximize-on-focus")
    set_max.add_argument("--enabled", choices=["true", "false"], required=True)

    sub.add_parser("targets")

    set_enabled = sub.add_parser("set-enabled-targets")
    set_enabled.add_argument("--names", nargs="+", required=True, help="Space-separated target names")

    set_target = sub.add_parser("set-target")
    set_target.add_argument("--name", required=True)

    test_target = sub.add_parser("test-target")
    test_target.add_argument("--name")

    rec = sub.add_parser("record-click")
    rec.add_argument("--seconds", type=int, default=4)

    rec_target = sub.add_parser("record-target-click")
    rec_target.add_argument("--name", required=True)
    rec_target.add_argument("--seconds", type=int, default=4)

    auto_cal = sub.add_parser("auto-calibrate-target")
    auto_cal.add_argument("--name", required=True)

    send_text = sub.add_parser("send-text")
    send_text.add_argument("--text")
    send_text.add_argument("--file")
    send_text.add_argument("--enter", action="store_true")

    send_img = sub.add_parser("send-image")
    send_img.add_argument("--path", required=True)
    send_img.add_argument("--enter", action="store_true")

    seq = sub.add_parser("run-sequence")
    seq.add_argument("--file", required=True)
    seq.add_argument("--test-mode", action="store_true", help="Type only; do not press Enter/send")

    run_job = sub.add_parser("run-job")
    run_job.add_argument("--dir", required=True)

    init_job = sub.add_parser("init-job")
    init_job.add_argument("--dir", required=True)
    init_job.add_argument("--brief", default="brief.md")
    init_job.add_argument("--design")
    init_job.add_argument("--target")
    init_job.add_argument("--name")
    init_job.add_argument("--force", action="store_true")
    init_job.add_argument(
        "--legacy-text-steps",
        action="store_true",
        help="Generate legacy text steps instead of worker_contract adapter steps",
    )

    materialize = sub.add_parser("materialize-app")
    materialize.add_argument("--source", required=True, help="Source markdown/text file that contains FILE blocks")
    materialize.add_argument("--out", required=True, help="Output directory for generated app files")

    dispatch_multi = sub.add_parser("dispatch-multi")
    dispatch_multi.add_argument("--file", required=True, help="JSON array of {target, content, press_enter?}")
    dispatch_multi.add_argument("--test-mode", action="store_true", help="Type only; do not press Enter/send")

    self_test = sub.add_parser("self-test-targets")
    self_test.add_argument("--names", nargs="+", help="Targets to test. Defaults to enabled targets")
    self_test.add_argument("--no-clear", action="store_true", help="Do not clear probe text after typing")
    self_test.add_argument("--no-open-commands", action="store_true", help="Do not use extension open commands during test")

    seq_test = sub.add_parser("test-sequence")
    seq_test.add_argument("--names", nargs="+", help="Target order to test. Defaults to copilot,gemini,codex,kilo,cline if present")
    seq_test.add_argument("--delay", type=float, default=1.0, help="Delay between targets in seconds")
    seq_test.add_argument("--prefix", default="KS_CODEOPS_SEQ", help="Prefix for typed test text")
    seq_test.add_argument("--open-commands", action="store_true", help="Allow extension open commands during test sequence")

    test_next = sub.add_parser("test-next")
    test_next.add_argument("--names", nargs="+", required=True, help="Ordered targets to test one-by-one")
    test_next.add_argument("--pause", type=float, default=1.0, help="Pause in seconds between targets")

    health = sub.add_parser("health-check")
    health.add_argument("--names", nargs="+", help="Targets to validate. Defaults to enabled targets")
    health.add_argument("--delay", type=float, default=1.0, help="Delay between sequence targets in seconds")
    health.add_argument("--prefix", default="KS_CODEOPS_HEALTH", help="Prefix for no-send sequence payload")
    health.add_argument("--open-commands", action="store_true", help="Allow extension open commands during probe and sequence")
    health.add_argument("--skip-focus", action="store_true", help="Skip focus pre-check")
    health.add_argument("--skip-probe", action="store_true", help="Skip per-target probe validation")
    health.add_argument("--skip-sequence", action="store_true", help="Skip no-send sequence validation")

    return parser


def main():
    args = build_parser().parse_args()
    config = AppConfig()

    if args.cmd == "version":
        print(__version__)
        return

    if args.cmd == "smoke-run":
        ok = _run_release_smoke(config=config, keep_temp=bool(args.keep_temp))
        if not ok:
            raise SystemExit(1)
        return

    automation = build_automation(config)
    sequencer = VSCodeSequencer(automation, config)
    sequencer.set_log_callback(print)

    if args.cmd == "windows":
        for title in automation.list_windows():
            _safe_print(title)
        return

    if args.cmd == "focus":
        if args.profile:
            config.focus_profile = args.profile
        if args.window_title:
            config.window_title = args.window_title
        if args.maximize and args.no_maximize:
            raise ValueError("Use only one of --maximize or --no-maximize")
        if args.maximize:
            config.maximize_on_focus = True
        if args.no_maximize:
            config.maximize_on_focus = False
        if args.profile or args.window_title or args.maximize or args.no_maximize:
            config.save()
        sequencer.test_focus()
        return

    if args.cmd == "set-window-title":
        config.window_title = args.title
        config.save()
        print(f"window_title set to: {config.window_title}")
        return

    if args.cmd == "set-maximize-on-focus":
        config.maximize_on_focus = args.enabled == "true"
        config.save()
        print(f"maximize_on_focus set to: {config.maximize_on_focus}")
        return

    if args.cmd == "targets":
        enabled = set(sequencer.enabled_targets())
        for name in sequencer.list_targets():
            marker = "*" if name == config.active_target else " "
            enabled_marker = "x" if name in enabled else " "
            print(f"{marker} [{enabled_marker}] {name}")
        return

    if args.cmd == "set-enabled-targets":
        sequencer.set_enabled_targets(args.names)
        return

    if args.cmd == "set-target":
        sequencer.set_active_target(args.name)
        return

    if args.cmd == "test-target":
        sequencer.activate_target(args.name)
        return

    if args.cmd == "record-click":
        sequencer.record_click(seconds=args.seconds)
        return

    if args.cmd == "record-target-click":
        sequencer.record_target_click(target_name=args.name, seconds=args.seconds)
        return

    if args.cmd == "auto-calibrate-target":
        ok = sequencer.auto_calibrate_target_click(args.name)
        print(f"{args.name}: {'ok' if ok else 'failed'}")
        if not ok:
            raise SystemExit(1)
        return

    if args.cmd == "send-text":
        content = args.text
        if args.file:
            with open(args.file, "r", encoding="utf-8") as handle:
                content = handle.read()
        if not content:
            raise ValueError("Provide --text or --file")
        sequencer.send_text(content, press_enter=args.enter)
        return

    if args.cmd == "send-image":
        sequencer.send_image(args.path, press_enter=args.enter)
        return

    if args.cmd == "run-sequence":
        sequencer.run_sequence(args.file, force_no_send=args.test_mode)
        return

    if args.cmd == "run-job":
        runner = JobRunner(sequencer, config)
        ok = runner.run_job(args.dir)
        if not ok:
            raise SystemExit(1)
        return

    if args.cmd == "init-job":
        builder = PlanBuilder(config)
        job_dir = args.dir
        brief_path = args.brief if os.path.isabs(args.brief) else os.path.join(job_dir, args.brief)
        design_path = None
        if args.design:
            design_path = args.design if os.path.isabs(args.design) else os.path.join(job_dir, args.design)
        project_name = args.name or os.path.basename(os.path.normpath(job_dir))
        plan = builder.create_plan(
            job_dir=job_dir,
            brief_path=brief_path,
            design_path=design_path,
            target_name=args.target,
            force=args.force,
            project_name=project_name,
            prefer_worker_contract=not bool(args.legacy_text_steps),
        )
        print(
            f"Created plan with {len(plan.get('steps', []))} steps at {job_dir}/plan.json "
            f"(assignment_policy={plan.get('assignment_policy', 'unknown')})"
        )
        return

    if args.cmd == "materialize-app":
        materializer = AppMaterializer()
        source = args.source
        out_dir = args.out
        if not os.path.isabs(source):
            source = os.path.join(os.getcwd(), source)
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(os.getcwd(), out_dir)
        written = materializer.materialize(source_file=source, output_dir=out_dir)
        print(f"Generated {len(written)} files in {out_dir}")
        for rel_path, full_path in written.items():
            print(f"- {rel_path} -> {full_path}")
        return

    if args.cmd == "dispatch-multi":
        with open(args.file, "r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            raise ValueError("dispatch-multi expects a JSON array")
        results = sequencer.dispatch_multi(
            payload,
            default_press_enter=config.auto_enter,
            force_no_send=args.test_mode,
        )
        for target, ok in results.items():
            print(f"{target}: {'ok' if ok else 'failed'}")
        return

    if args.cmd == "self-test-targets":
        targets = args.names or sequencer.enabled_targets()
        if not targets:
            raise ValueError("No targets provided and no enabled targets found")
        all_ok = True
        for target in targets:
            probe_text = f"KS_CODEOPS_PROBE_{target.upper()}"
            if args.no_open_commands:
                allow_open = False
            else:
                allow_open = bool(sequencer._target_payload(target).get("command_open_in_test", False))
            ok = sequencer.probe_target_input(
                target,
                probe_text,
                clear_after=not args.no_clear,
                allow_command_open=allow_open,
            )
            all_ok = all_ok and ok
            print(f"{target}: {'ok' if ok else 'failed'}")
        if not all_ok:
            raise SystemExit(1)
        return

    if args.cmd == "test-sequence":
        if args.names:
            targets = args.names
        else:
            preferred = ["copilot", "gemini", "codex", "kilo", "cline"]
            targets = [name for name in preferred if name in sequencer.list_targets()]
            if not targets:
                targets = sequencer.list_targets()
        results = sequencer.run_target_test_sequence(
            targets=targets,
            delay_between_s=max(0.0, float(args.delay)),
            text_prefix=args.prefix,
            allow_command_open=bool(args.open_commands),
        )
        all_ok = True
        for name in targets:
            ok = bool(results.get(name))
            all_ok = all_ok and ok
            print(f"{name}: {'pass' if ok else 'fail'}")
        if not all_ok:
            raise SystemExit(1)
        return

    if args.cmd == "test-next":
        results = sequencer.test_targets_next(args.names, pause_s=max(0.0, float(args.pause)))
        all_ok = True
        for target, ok in results.items():
            print(f"{target}: {'ok' if ok else 'failed'}")
            all_ok = all_ok and ok
        if not all_ok:
            raise SystemExit(1)
        return

    if args.cmd == "health-check":
        targets = args.names or sequencer.enabled_targets()
        if not targets:
            targets = sequencer.list_targets()
        if not targets:
            raise ValueError("No targets available for health-check")

        overall_ok = True
        health_report = {
            "checked_at": datetime.now().isoformat(),
            "open_commands": bool(args.open_commands),
            "focus": {"skipped": bool(args.skip_focus), "ok": None},
            "probe": {"skipped": bool(args.skip_probe)},
            "sequence": {"skipped": bool(args.skip_sequence)},
            "targets": {},
        }

        print("== KS CodeOps Health Check ==")
        print(f"Targets: {', '.join(targets)}")
        if not args.open_commands and len(targets) > 1:
            print(
                "note: safe mode is enabled (no open commands). "
                "Only first target can be strictly verified; later targets will fail as unverifiable."
            )

        if args.skip_focus:
            print("focus: skipped")
            health_report["focus"]["ok"] = None
        else:
            focus_ok = sequencer.test_focus()
            print(f"focus: {'ok' if focus_ok else 'failed'}")
            overall_ok = overall_ok and bool(focus_ok)
            health_report["focus"]["ok"] = bool(focus_ok)

        if args.skip_probe:
            print("probe: skipped")
            for target in targets:
                entry = health_report["targets"].setdefault(target, {})
                entry["probe_ok"] = None
        else:
            probe_all_ok = True
            for target in targets:
                probe_text = f"KS_CODEOPS_HEALTH_PROBE_{target.upper()}"
                allow_open = bool(args.open_commands and sequencer._target_payload(target).get("command_open_in_test", False))
                ok = sequencer.probe_target_input(
                    target,
                    probe_text,
                    clear_after=True,
                    allow_command_open=allow_open,
                )
                probe_all_ok = probe_all_ok and bool(ok)
                print(f"probe[{target}]: {'ok' if ok else 'failed'}")
                entry = health_report["targets"].setdefault(target, {})
                entry["probe_ok"] = bool(ok)
            overall_ok = overall_ok and probe_all_ok

        if args.skip_sequence:
            print("sequence: skipped")
            for target in targets:
                entry = health_report["targets"].setdefault(target, {})
                entry["sequence_ok"] = None
        else:
            seq_results = sequencer.run_target_test_sequence(
                targets=targets,
                delay_between_s=max(0.0, float(args.delay)),
                text_prefix=args.prefix,
                allow_command_open=bool(args.open_commands),
            )
            seq_all_ok = True
            for target in targets:
                ok = bool(seq_results.get(target))
                seq_all_ok = seq_all_ok and ok
                print(f"sequence[{target}]: {'pass' if ok else 'fail'}")
                entry = health_report["targets"].setdefault(target, {})
                entry["sequence_ok"] = bool(ok)
            overall_ok = overall_ok and seq_all_ok

        healthy_targets = []
        for target in targets:
            entry = health_report["targets"].setdefault(target, {})
            probe_ok = entry.get("probe_ok")
            sequence_ok = entry.get("sequence_ok")
            healthy = True
            if probe_ok is not None:
                healthy = healthy and bool(probe_ok)
            if sequence_ok is not None:
                healthy = healthy and bool(sequence_ok)
            if probe_ok is None and sequence_ok is None:
                healthy = bool(overall_ok)
            entry["healthy"] = bool(healthy)
            if entry["healthy"]:
                healthy_targets.append(target)

        health_report["overall_ok"] = bool(overall_ok)
        health_report["healthy_targets"] = healthy_targets

        health_file = str(getattr(config, "target_health_file", "target_health.json"))
        if not os.path.isabs(health_file):
            health_file = os.path.join(os.getcwd(), health_file)
        health_dir = os.path.dirname(health_file)
        if health_dir:
            os.makedirs(health_dir, exist_ok=True)
        with open(health_file, "w", encoding="utf-8") as handle:
            json.dump(health_report, handle, indent=2)
        print(f"health-snapshot: {health_file}")

        print(f"health-check: {'PASS' if overall_ok else 'FAIL'}")
        if not overall_ok:
            raise SystemExit(1)
        return


if __name__ == "__main__":
    main()
