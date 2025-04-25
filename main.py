from collections import defaultdict, deque
import  graphviz

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
        Expected file format:
          States: q0,q1,q2
          Alphabet: a,b
          Start: q0
          Accept: q2
          Transitions:
            q0,a->q0,q1
            q0,b->q0
            q1,b->q2
            q2,->q0  # epsilon move
        """
        states, alphabet, transitions = set(), set(), {}
        start, accept = None, set()
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
                    left, right = line.split('->')
                    s, sym = (x.strip() for x in left.split(','))
                    dests = [x.strip() for x in right.split(',') if x.strip()]
                    transitions[(s, sym)] = set(dests)
        return NFA(states, alphabet, transitions, start, accept)


def epsilon_closure(nfa: NFA, state_set: set) -> set:
    """Compute epsilon-closure for a set of NFA states"""
    stack, closure = list(state_set), set(state_set)
    while stack:
        s = stack.pop()
        for nxt in nfa.transitions.get((s, ''), []):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure


def move(nfa: NFA, state_set: set, symbol: str) -> set:
    """Given NFA states and an input symbol, return reachable states (excluding ε)"""
    result = set()
    for s in state_set:
        result |= nfa.transitions.get((s, symbol), set())
    return result


def nfa_to_dfa(nfa: NFA):
    """Subset construction converting NFA to DFA"""
    dfa_states, dfa_trans, dfa_accept = set(), {}, set()
    alpha = nfa.alphabet.copy()
    start = frozenset(epsilon_closure(nfa, {nfa.start_state}))
    queue = deque([start]); dfa_states.add(start)
    if nfa.accept_states & set(start): dfa_accept.add(start)
    while queue:
        curr = queue.popleft()
        for sym in alpha:
            mv = move(nfa, curr, sym)
            if not mv: continue
            nxt = frozenset(epsilon_closure(nfa, mv))
            dfa_trans[(curr, sym)] = nxt
            if nxt not in dfa_states:
                dfa_states.add(nxt); queue.append(nxt)
                if nfa.accept_states & set(nxt): dfa_accept.add(nxt)
    return dfa_states, alpha, dfa_trans, start, dfa_accept


def visualize_automaton(states, transitions, start_state, accept_states, title='Automaton', filename=None):
    """
    Render automaton using Graphviz.
    - states: iterable of state identifiers
    - transitions: dict (state, symbol) -> next_state(s)
    - start_state: start identifier
    - accept_states: iterable of accept identifiers
    - title: graph title
    - filename: if provided, save as DOT and PNG with this name
    Returns: graphviz.Digraph object
    """
    def cleanstr(s:str):
        s=str(s)
        return s.strip().strip("frozenset").strip("(").strip(")").strip("\'").strip('\"').strip("{").strip("}").replace("'",'')

    font="Times New Roman Bold"
    dot = graphviz.Digraph(    
        comment=title,
        format='png',
        graph_attr={'dpi': '600', 'rankdir': 'LR', 'nodesep': '0.5', 'ranksep': '0.75'},
        node_attr={'fontname': font},
        edge_attr={'fontname': font}
    )

    # Add nodes
    for s in states:
        label = cleanstr(s)
        shape = 'doublecircle' if s in accept_states else 'circle'
        dot.node(label, label=label, shape=shape)

    # Invisible start arrow
    dot.node('_start', shape='none', label='')
    dot.edge('_start', cleanstr(start_state), label='start')

    # Add transitions
    for (src, sym), dsts in transitions.items():
        src_lbl = cleanstr(src)
        if isinstance(dsts, (set, list)):
            for d in dsts:
                dot.edge(src_lbl, cleanstr(d), label=sym or 'ε')
        else:
            dot.edge(src_lbl, cleanstr(dsts), label=sym or 'ε')

    if filename:
        dot.render(filename, format='png', cleanup=True)
    return dot

if __name__ == '__main__':
    # Example usage
    for fname in ['example3.txt']:
        nfa = NFA.parse_from_file(fname)
        dfa_states, dfa_alpha, dfa_trans, dfa_start, dfa_accept = nfa_to_dfa(nfa)
        # Visualize NFA
        nfa_dot = visualize_automaton(nfa.states, nfa.transitions, nfa.start_state, nfa.accept_states,
                                     title=f'NFA_{fname}', filename=f'nfa_{fname}')
        # Visualize DFA
        # Flatten frozensets for labeling
        str_states = {frozenset(s): frozenset(s) for s in dfa_states}
        dfa_dot = visualize_automaton(
            dfa_states, dfa_trans, dfa_start, dfa_accept,
            title=f'DFA_{fname}', filename=f'dfa_{fname}'
        )
