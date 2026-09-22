from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any, Callable


@dataclass(frozen=True)
class TestCase:
    data: Any
    public: bool = False


@dataclass(frozen=True)
class Problem:
    slug: str
    title: str
    difficulty: str
    statement: str
    signature: str
    starter_code: str
    examples: list[dict[str, Any]]
    tests: list[TestCase]
    expected: Callable[[Any], Any]


def _suffix_array_reference(s: str) -> list[int]:
    n = len(s)
    if n == 0:
        return []
    sa = list(range(n))
    rank = [ord(c) for c in s]
    k = 1
    while k < n:
        sa.sort(key=lambda i: (rank[i], rank[i + k] if i + k < n else -1))
        nxt = [0] * n
        classes = 0
        nxt[sa[0]] = 0
        for p in range(1, n):
            a, b = sa[p - 1], sa[p]
            ka = (rank[a], rank[a + k] if a + k < n else -1)
            kb = (rank[b], rank[b + k] if b + k < n else -1)
            if ka != kb:
                classes += 1
            nxt[b] = classes
        rank = nxt
        if classes == n - 1:
            break
        k <<= 1
    return sa


def _lcs_reference(pair: tuple[str, str]) -> int:
    a, b = pair
    # Suffix automaton for O(|a| + |b|) reference grading.
    nexts: list[dict[str, int]] = [{}]
    link = [-1]
    length = [0]
    last = 0
    for ch in a:
        cur = len(nexts)
        nexts.append({})
        link.append(0)
        length.append(length[last] + 1)
        p = last
        while p >= 0 and ch not in nexts[p]:
            nexts[p][ch] = cur
            p = link[p]
        if p == -1:
            link[cur] = 0
        else:
            q = nexts[p][ch]
            if length[p] + 1 == length[q]:
                link[cur] = q
            else:
                clone = len(nexts)
                nexts.append(dict(nexts[q]))
                link.append(link[q])
                length.append(length[p] + 1)
                while p >= 0 and nexts[p].get(ch) == q:
                    nexts[p][ch] = clone
                    p = link[p]
                link[q] = link[cur] = clone
        last = cur

    state = size = best = 0
    for ch in b:
        while state and ch not in nexts[state]:
            state = link[state]
            size = min(size, length[state])
        if ch in nexts[state]:
            state = nexts[state][ch]
            size += 1
        else:
            state = 0
            size = 0
        best = max(best, size)
    return best


def _trie_reference(case: list[tuple[str, str]]) -> list[bool]:
    root: dict[str, Any] = {}
    terminal = "\0"
    out: list[bool] = []
    for op, value in case:
        if op == "insert":
            node = root
            for ch in value:
                node = node.setdefault(ch, {})
            node[terminal] = True
        elif op in {"search", "starts_with"}:
            node = root
            found = True
            for ch in value:
                if ch not in node:
                    found = False
                    break
                node = node[ch]
            out.append(found and (op == "starts_with" or terminal in node))
        else:
            raise ValueError(f"Unknown trie operation: {op}")
    return out


def _pattern(length: int, alphabet: str, seed: int) -> str:
    rng = Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(length))


def _trie_case(word_count: int, query_count: int, seed: int) -> list[tuple[str, str]]:
    rng = Random(seed)
    alphabet = "abcdefghi"
    words: list[str] = []
    ops: list[tuple[str, str]] = []
    for i in range(word_count):
        stem = "".join(rng.choice(alphabet) for _ in range(3 + (i % 9)))
        word = f"{stem}{i:x}"
        words.append(word)
        ops.append(("insert", word))
        if i % 11 == 0:
            ops.append(("insert", word))  # duplicate insert must be harmless
    for i in range(query_count):
        word = words[(i * 17 + 3) % len(words)]
        if i % 4 == 0:
            ops.append(("search", word))
        elif i % 4 == 1:
            ops.append(("search", word + "z"))
        elif i % 4 == 2:
            ops.append(("starts_with", word[: max(1, len(word) // 2)]))
        else:
            ops.append(("starts_with", "zz" + word[:2]))
    return ops


SUFFIX_TESTS = [
    TestCase("a", True),
    TestCase("aaaa", True),
    TestCase("banana"),
    TestCase("mississippi"),
    TestCase("abracadabra" * 4),
    TestCase(_pattern(128, "abcd", 11)),
    TestCase((_pattern(128, "abcde", 22) + "banana") * 4),
    TestCase(_pattern(1500, "abcdef", 33)),
    TestCase(_pattern(12000, "abcdefgh", 44)),
    TestCase(_pattern(60000, "abcdefghijklmnop", 55)),
]

LCS_TESTS = [
    TestCase(("a", "a"), True),
    TestCase(("abc", "zab"), True),
    TestCase(("banana", "ananas")),
    TestCase(("abcdef", "xyzuvw")),
    TestCase(("ababa" * 20, "babab" * 20)),
    TestCase((_pattern(180, "abcd", 61), _pattern(170, "abcd", 62))),
    TestCase(("x" * 240 + "algorithm" + "y" * 240, "q" * 180 + "algorithm" + "r" * 320)),
    TestCase((_pattern(1200, "abcdef", 71), _pattern(1300, "abcdef", 72))),
    TestCase((_pattern(4000, "abcdefgh", 81) + "datastructures", _pattern(4200, "abcdefgh", 82) + "datastructures")),
    TestCase((_pattern(8000, "abcdefghijkl", 91) + "computationalgeometry", _pattern(8500, "abcdefghijkl", 92) + "computationalgeometry")),
]

TRIE_TESTS = [
    TestCase([("insert", "apple"), ("search", "apple")], True),
    TestCase([("insert", "apple"), ("search", "app"), ("starts_with", "app"), ("insert", "app"), ("search", "app")], True),
    TestCase([("insert", "a"), ("insert", "ab"), ("insert", "abc"), ("search", "abcd"), ("starts_with", "abc")]),
    TestCase([("insert", "same"), ("insert", "same"), ("search", "same"), ("starts_with", "sam"), ("search", "sam")]),
    TestCase(_trie_case(30, 50, 101)),
    TestCase(_trie_case(100, 180, 102)),
    TestCase(_trie_case(300, 500, 103)),
    TestCase(_trie_case(800, 1300, 104)),
    TestCase(_trie_case(2500, 4000, 105)),
    TestCase(_trie_case(12000, 20000, 106)),
]


PROBLEMS: dict[str, Problem] = {
    "suffix-array": Problem(
        slug="suffix-array",
        title="Suffix Array",
        difficulty="Hard",
        statement=(
            "Implementa un suffix array. Recibes una cadena no vacía `s` y debes devolver una lista con "
            "todos los índices iniciales de sus sufijos, ordenados lexicográficamente por el sufijo correspondiente. "
            "Los índices son 0-based. Los casos finales usan cadenas grandes: una solución que materializa y ordena "
            "todos los sufijos completos puede exceder los límites."
        ),
        signature="def suffix_array(s: str) -> list[int]:",
        starter_code="def suffix_array(s: str) -> list[int]:\n    # Escribe tu solución aquí\n    pass\n",
        examples=[
            {"input": 's = "banana"', "output": "[5, 3, 1, 0, 4, 2]"},
            {"input": 's = "aaaa"', "output": "[3, 2, 1, 0]"},
        ],
        tests=SUFFIX_TESTS,
        expected=_suffix_array_reference,
    ),
    "longest-common-substring": Problem(
        slug="longest-common-substring",
        title="Longest Common Substring",
        difficulty="Hard",
        statement=(
            "Dadas dos cadenas `a` y `b`, devuelve la longitud de su subcadena contigua común más larga. "
            "Una subcadena debe ocupar posiciones consecutivas; no es una subsecuencia. Devuelve 0 cuando no exista "
            "ningún carácter común. Los casos finales son suficientemente grandes para penalizar DP cuadrática lenta."
        ),
        signature="def longest_common_substring(a: str, b: str) -> int:",
        starter_code="def longest_common_substring(a: str, b: str) -> int:\n    # Devuelve solamente la longitud\n    pass\n",
        examples=[
            {"input": 'a = "banana", b = "ananas"', "output": "5"},
            {"input": 'a = "abc", b = "xyz"', "output": "0"},
        ],
        tests=LCS_TESTS,
        expected=_lcs_reference,
    ),
    "trie": Problem(
        slug="trie",
        title="Trie",
        difficulty="Medium",
        statement=(
            "Implementa la clase `Trie` con `insert(word)`, `search(word)` y `starts_with(prefix)`. "
            "`search` debe ser verdadero solo si la palabra completa fue insertada; `starts_with` comprueba prefijos. "
            "Las inserciones duplicadas deben ser seguras. Las pruebas finales ejecutan miles de operaciones."
        ),
        signature="class Trie:  # insert, search, starts_with",
        starter_code=(
            "class Trie:\n"
            "    def __init__(self):\n"
            "        pass\n\n"
            "    def insert(self, word: str) -> None:\n"
            "        pass\n\n"
            "    def search(self, word: str) -> bool:\n"
            "        pass\n\n"
            "    def starts_with(self, prefix: str) -> bool:\n"
            "        pass\n"
        ),
        examples=[
            {"input": 'insert("apple"), search("apple")', "output": "True"},
            {"input": 'insert("apple"), search("app"), starts_with("app")', "output": "False, True"},
        ],
        tests=TRIE_TESTS,
        expected=_trie_reference,
    ),
}


def public_problem(problem: Problem) -> dict[str, Any]:
    return {
        "slug": problem.slug,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "statement": problem.statement,
        "signature": problem.signature,
        "starter_code": problem.starter_code,
        "examples": problem.examples,
        "test_count": len(problem.tests),
        "public_test_count": sum(case.public for case in problem.tests),
    }
