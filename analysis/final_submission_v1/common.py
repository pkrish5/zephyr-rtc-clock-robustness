"""Standard-library helpers for read-only final submission analysis."""
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda: stream.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


class Inputs:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.hashes = {}

    def path(self, relative):
        path = (self.root / relative).resolve()
        path.relative_to(self.root)
        return path

    def use(self, relative):
        path = self.path(relative)
        key = str(path.relative_to(self.root))
        digest = sha(path)
        if key in self.hashes:
            assert self.hashes[key] == digest, key
        self.hashes[key] = digest
        return path

    def json(self, relative):
        return json.loads(self.use(relative).read_text())

    def csv(self, relative):
        with self.use(relative).open(newline='') as stream:
            return list(csv.DictReader(stream))

    def text(self, relative):
        return self.use(relative).read_text()

    def finish(self):
        assert all(sha(self.root / path) == digest for path, digest in self.hashes.items())
        return dict(sorted(self.hashes.items()))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def csv_save(path, rows, fields=None):
    path = Path(path)
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                         for key, value in row.items()} for row in rows)


def fisher(a, b, c, d):
    """Two-sided Fisher exact p; sum tables no likelier than the observed."""
    first, second, successes = a + b, c + d, a + c
    denominator = math.comb(first + second, successes)
    probability = lambda k: Fraction(math.comb(first, k) * math.comb(second, successes - k), denominator)
    observed = probability(a)
    p = sum((probability(k) for k in range(max(0, successes - second), min(first, successes) + 1)
             if probability(k) <= observed), Fraction(0))
    return dict(table=[[a, b], [c, d]], two_sided_p=float(p), exact_fraction=str(p))


def wilson(successes, n):
    if not n:
        return [None, None]
    z = NormalDist().inv_cdf(.975)
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0, center - half), min(1, center + half)]


def failure_share(boundary_hz, distribution, conditional_legal=True):
    """Illustrative step-model CDF, never a measured device distribution."""
    lower, upper = 17000., 47000.
    if distribution == 'uniform':
        return max(0., min(1., (boundary_hz - lower) / (upper - lower)))
    sigma = {'normal_3sigma': 5000., 'normal_2sigma': 7500.}[distribution]
    cdf = NormalDist(32000., sigma).cdf
    if not conditional_legal:
        return cdf(boundary_hz)
    clipped = max(lower, min(upper, boundary_hz))
    return (cdf(clipped) - cdf(lower)) / (cdf(upper) - cdf(lower))


def markdown_table(rows, columns):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    header = '| ' + ' | '.join(label for _, label in columns) + ' |\n'
    line = '| ' + ' | '.join('---' for _ in columns) + ' |\n'
    body = ''.join('| ' + ' | '.join(cell(row.get(key, '')) for key, _ in columns) + ' |\n' for row in rows)
    return header + line + body
