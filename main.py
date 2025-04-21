import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict, deque

class NFA:
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        """
        states: set of state names (strings)
        alphabet: set of input symbols (exclude epsilon)
        transitions: dict of (state, symbol) -> set of next states; use '' for epsilon
        start_state: string
        accept_states: set of state names
        """
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = defaultdict(set)
        for (s, sym), dests in transitions.items():
            self.transitions[(s, sym)] |= set(dests)
        self.start_state = start_state
        self.accept_states = set(accept_states)

    @staticmethod
    def parse_from_file(path):
        """
        Expected format in text file:
        States: q0,q1,q2
        Alphabet: a,b
        Start: q0
        Accept: q2
        Transitions:
        q0,a->q0,q1
        q0,b->q0
        q1,b->q2
        q2,->q0  # epsilon move, symbol empty before comma
        """
        states = set()
        alphabet = set()
        transitions = {}
        start = None
        accept = set()
        with open(path) as f:
            section = None
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.startswith('States:'):
                    states = set(x.strip() for x in line.split(':',1)[1].split(','))
                elif line.startswith('Alphabet:'):
                    alphabet = set(x.strip() for x in line.split(':',1)[1].split(','))
                elif line.startswith('Start:'):
                    start = line.split(':',1)[1].strip()
                elif line.startswith('Accept:'):
                    accept = set(x.strip() for x in line.split(':',1)[1].split(','))
                elif line.startswith('Transitions:'):
                    section = 'trans'
                elif section == 'trans':
                    # parse transition line
                    left, right = line.split('->')
                    s, sym = left.split(',')
                    sym = sym.strip()
                    dests = [x.strip() for x in right.split(',') if x.strip()]
                    transitions[(s.strip(), sym)] = set(dests)
        return NFA(states, alphabet, transitions, start, accept)


def epsilon_closure(nfa: NFA, state_set: set) -> set:
    """
    Compute epsilon-closure for a set of NFA states
    """
    stack = list(state_set)
    closure = set(state_set)
    while stack:
        s = stack.pop()
        for nxt in nfa.transitions.get((s, ''), []):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure


def move(nfa: NFA, state_set: set, symbol: str) -> set:
    """
    For a set of NFA states and an input symbol, find the set of next states (excluding epsilon)
    """
    result = set()
    for s in state_set:
        result |= nfa.transitions.get((s, symbol), set())
    return result


def nfa_to_dfa(nfa: NFA):
    """
    Convert an NFA to an equivalent DFA using subset construction.
    Returns: (dfa_states, dfa_alphabet, dfa_transitions, dfa_start, dfa_accept)
    - dfa_states: set of frozensets of NFA states
    - dfa_alphabet: same as NFA.alphabet
    - dfa_transitions: dict (frozenset, symbol) -> frozenset
    - dfa_start: frozenset
    - dfa_accept: set of frozensets
    """
    dfa_states = set()
    dfa_transitions = {}
    dfa_accept = set()
    dfa_alphabet = nfa.alphabet.copy()
    start_closure = frozenset(epsilon_closure(nfa, {nfa.start_state}))
    queue = deque([start_closure])
    dfa_states.add(start_closure)
    if nfa.accept_states & set(start_closure):
        dfa_accept.add(start_closure)
    while queue:
        current = queue.popleft()
        for sym in dfa_alphabet:
            # move then closure
            mv = move(nfa, current, sym)
            if not mv:
                continue
            c = frozenset(epsilon_closure(nfa, mv))
            dfa_transitions[(current, sym)] = c
            if c not in dfa_states:
                dfa_states.add(c)
                queue.append(c)
                if nfa.accept_states & set(c):
                    dfa_accept.add(c)
    return dfa_states, dfa_alphabet, dfa_transitions, start_closure, dfa_accept


def visualize_automaton(states, transitions, start_state, accept_states, title='Automaton'):
    """
    Visualize automaton (NFA or DFA) using networkx and matplotlib
    states: iterable of state identifiers
    transitions: dict (state, symbol) -> next_state
    start_state: single state
    accept_states: set of states
    """
    G = nx.DiGraph()
    for s in states:
        G.add_node(s.strip("frozenset").strip("(").strip(")"))
    for (s, sym), t in transitions.items():
        if type(t)!=str:
            for dst in list(t):
                G.add_edge(s, dst, label=sym)
        else:
            G.add_edge(s.strip("frozenset").strip("(").strip(")"), t.strip("frozenset").strip("(").strip(")"), label=sym)

    pos = nx.spring_layout(G)
    plt.figure(figsize=(9, 8))
    # draw nodes
    nx.draw_networkx_nodes(G, pos,
                           node_color=['lightblue' if s in accept_states else 'white' for s in G.nodes()],
                           edgecolors='black')
    # draw edges
    nx.draw_networkx_edges(G, pos, connectionstyle='arc3, rad=0.1', arrowsize=80)
    # labels
    nx.draw_networkx_labels(G, pos)
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    # mark start
    plt.title(title)
    plt.axis('off')
    plt.show()
    print(f"States: {states}")

if __name__ == '__main__':
    # Example usage with two files
    for fname in ['example1.txt', 'example2.txt']:
        print(f"\nLoading NFA from {fname}")
        nfa = NFA.parse_from_file(fname)
        dfa_states, dfa_alpha, dfa_trans, dfa_start, dfa_accept = nfa_to_dfa(nfa)
        visualize_automaton(nfa.states, nfa.transitions, nfa.start_state, nfa.accept_states,
                            title=f"NFA from {fname}")
        # For DFA, convert frozensets to strings for readability
        str_states = {str(s) for s in dfa_states}
        str_trans = {(str(s), sym): str(t) for (s, sym), t in dfa_trans.items()}
        visualize_automaton(str_states, str_trans, str(dfa_start), set(str(s) for s in dfa_accept),
                            title=f"DFA from {fname}")
