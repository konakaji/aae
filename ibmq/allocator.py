from qiskit.transpiler import Layout
import copy


class QubitAllocator:
    def __init__(self, n_qubit):
        self.n_qubit = n_qubit

    def allocate(self, couplings):
        nodes = self._get_nodes(couplings)
        if len(nodes) < self.n_qubit:
            raise CannotAllocateException("the number of qubits is larger than the number of nodes")
        edges = self._get_edges(couplings)
        return self._do_allocate(nodes, edges)

    def _do_allocate(self, nodes, edges):
        pass

    def _get_nodes(self, couplings):
        nodes = set()
        for cs in couplings:
            for c in cs:
                nodes.add(c)
        return nodes

    def _get_edges(self, couplings):
        result = {}
        for c in couplings:
            if c[0] not in result:
                result[c[0]] = []
            result[c[0]].append(c[1])
            if c[1] not in result:
                result[c[1]] = []
            result[c[1]].append(c[0])
        return result


class NaiveQubitAllocator(QubitAllocator):
    def _do_allocate(self, nodes, edges):
        current = None
        for n in nodes:
            path = self._get_longest_path(n, edges)
            if len(path) == self.n_qubit:
                return path
            if current is None or len(path) > len(current):
                current = path
        for n in nodes:
            if not self._is_included(n, current):
                current.append(n)
            if len(current) == self.n_qubit:
                return current
        return current

    def _finalize(self, path):
        result = {}
        for i in range(self.n_qubit):
            result[i] = path
        return Layout(result)

    def _get_longest_path(self, node, edge_map):
        path = [node]
        paths = []
        self._build_paths(paths, node, path, edge_map)
        result = None
        for p in paths:
            if result is None or len(p) > len(result):
                result = p
                if len(result) == self.n_qubit:
                    return result
        return result

    def _build_paths(self, paths: [[]], current_node, current_path, edge_map):
        if len(current_path) == self.n_qubit:
            paths.append(current_path)
            return
        new_node_exists = False
        for new_node in edge_map[current_node]:
            if not self._is_included(new_node, current_path):
                p = copy.copy(current_path)
                p.append(new_node)
                self._build_paths(paths, new_node, p, edge_map)
                new_node_exists = True
        if not new_node_exists:
            paths.append(current_path)

    def _is_included(self, node, path):
        for n in path:
            if n == node:
                return True
        return False


class CannotAllocateException(Exception):
    pass
