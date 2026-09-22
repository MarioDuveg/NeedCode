from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any

from .problems import Problem

MAX_CODE_CHARS = 20_000
WALL_TIMEOUT_SECONDS = 1.8
MEMORY_LIMIT_MB = 256
OUTPUT_LIMIT_CHARS = 32_000
_EXPECTED_CACHE: dict[tuple[str, int], tuple[Any, str]] = {}

FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "vars",
    "dir",
    "breakpoint",
    "help",
}


class SubmissionRejected(ValueError):
    pass


def validate_source(code: str) -> None:
    if not code.strip():
        raise SubmissionRejected("El código está vacío.")
    if len(code) > MAX_CODE_CHARS:
        raise SubmissionRejected(f"El código excede {MAX_CODE_CHARS} caracteres.")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SubmissionRejected(f"SyntaxError: {exc.msg} (línea {exc.lineno}).") from exc

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SubmissionRejected("No se permiten imports en las soluciones.")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise SubmissionRejected("No se permite acceso a atributos dunder.")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise SubmissionRejected("No se permite acceso directo a nombres dunder.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            raise SubmissionRejected(f"No se permite llamar a {node.func.id}().")


HARNESS = r'''
import hashlib, json, sys, time

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "chr": chr,
    "dict": dict, "enumerate": enumerate, "filter": filter, "float": float,
    "int": int, "len": len, "list": list, "map": map, "max": max,
    "min": min, "object": object, "ord": ord, "pow": pow, "range": range,
    "reversed": reversed, "round": round, "set": set, "slice": slice,
    "sorted": sorted, "str": str, "sum": sum, "super": super, "tuple": tuple,
    "zip": zip, "Exception": Exception, "ValueError": ValueError,
    "TypeError": TypeError, "IndexError": IndexError, "KeyError": KeyError,
    "RuntimeError": RuntimeError, "__build_class__": __build_class__,
}

payload = json.loads(sys.stdin.read())
namespace = {"__builtins__": SAFE_BUILTINS, "__name__": "submission"}
started = time.perf_counter()
try:
    exec(payload["code"], namespace, namespace)
    slug = payload["slug"]
    data = payload["data"]
    if slug == "suffix-array":
        fn = namespace.get("suffix_array")
        if not callable(fn):
            raise TypeError("Debes definir suffix_array(s).")
        result = fn(data)
    elif slug == "longest-common-substring":
        fn = namespace.get("longest_common_substring")
        if not callable(fn):
            raise TypeError("Debes definir longest_common_substring(a, b).")
        result = fn(data[0], data[1])
    elif slug == "trie":
        cls = namespace.get("Trie")
        if not isinstance(cls, type):
            raise TypeError("Debes definir la clase Trie.")
        trie = cls()
        result = []
        for op, value in data:
            if op == "insert":
                trie.insert(value)
            elif op == "search":
                result.append(bool(trie.search(value)))
            elif op == "starts_with":
                result.append(bool(trie.starts_with(value)))
    else:
        raise ValueError("Problema desconocido.")
    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    preview = result if len(encoded) <= 2000 else None
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(json.dumps({"ok": True, "digest": digest, "preview": preview, "elapsed_ms": elapsed_ms}, ensure_ascii=False))
except BaseException as exc:
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}", "elapsed_ms": elapsed_ms}, ensure_ascii=False))
'''


@dataclass
class CaseResult:
    case: int
    passed: bool
    public: bool
    elapsed_ms: float | None = None
    error: str | None = None
    expected: Any | None = None
    received: Any | None = None


def _resource_limiter() -> None:
    # Linux/Unix only; Render's Docker runtime is Linux.
    try:
        import resource

        memory = MEMORY_LIMIT_MB * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    except Exception:
        pass


def _run_one(problem: Problem, code: str, case_index: int) -> CaseResult:
    case = problem.tests[case_index]
    payload = {"slug": problem.slug, "code": code, "data": case.data}
    cache_key = (problem.slug, case_index)
    cached = _EXPECTED_CACHE.get(cache_key)
    if cached is None:
        import hashlib

        expected = problem.expected(case.data)
        expected_encoded = json.dumps(expected, ensure_ascii=False, separators=(",", ":"))
        expected_digest = hashlib.sha256(expected_encoded.encode("utf-8")).hexdigest()
        _EXPECTED_CACHE[cache_key] = (expected, expected_digest)
    else:
        expected, expected_digest = cached

    try:
        with tempfile.TemporaryDirectory(prefix="algograder-") as tmp:
            proc = subprocess.run(
                [sys.executable, "-I", "-S", "-c", HARNESS],
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                cwd=tmp,
                timeout=WALL_TIMEOUT_SECONDS,
                env={"PATH": os.environ.get("PATH", "")},
                preexec_fn=_resource_limiter if os.name == "posix" else None,
            )
    except subprocess.TimeoutExpired:
        return CaseResult(case_index + 1, False, case.public, error="Time Limit Exceeded")

    stdout = proc.stdout[-OUTPUT_LIMIT_CHARS:].strip()
    if not stdout:
        err = (proc.stderr or "Proceso terminado sin salida").strip()[-500:]
        return CaseResult(case_index + 1, False, case.public, error=err)

    try:
        data = json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError:
        return CaseResult(case_index + 1, False, case.public, error="Salida inválida del ejecutor.")

    if not data.get("ok"):
        return CaseResult(
            case_index + 1,
            False,
            case.public,
            elapsed_ms=round(float(data.get("elapsed_ms", 0)), 2),
            error=str(data.get("error", "Runtime Error"))[:500],
        )

    received = data.get("preview")
    passed = data.get("digest") == expected_digest
    return CaseResult(
        case_index + 1,
        passed,
        case.public,
        elapsed_ms=round(float(data.get("elapsed_ms", 0)), 2),
        expected=expected if case.public and not passed else None,
        received=received if case.public and not passed else None,
        error=None if passed else "Wrong Answer",
    )


def judge(problem: Problem, code: str) -> dict[str, Any]:
    validate_source(code)
    started = time.perf_counter()
    results = [_run_one(problem, code, i) for i in range(len(problem.tests))]
    passed = sum(r.passed for r in results)
    score = passed  # exactly 10 cases -> score out of 10
    return {
        "problem": problem.slug,
        "passed": passed,
        "total": len(results),
        "score": score,
        "max_score": 10,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "cases": [
            {
                "case": r.case,
                "passed": r.passed,
                "public": r.public,
                "elapsed_ms": r.elapsed_ms,
                "error": r.error,
                "expected": r.expected,
                "received": r.received,
            }
            for r in results
        ],
    }
