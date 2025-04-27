import streamlit as st
from collections import defaultdict, deque
import graphviz

# ------------------------
# Core classes and logic
# ------------------------

class NFA:
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = defaultdict(set)
        for (s, sym), dests in transitions.items():
            self.transitions[(s, sym)] |= set(dests)
        self.start_state = start_state
        self.accept_states = set(accept_states)

    @staticmethod
    def parse_from_text(text):
        """Parse NFA from text representation."""
        states, alphabet, transitions = set(), set(), {}
        start, accept = None, set()
        lines = text.strip().splitlines()
        section = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('States:'):
                states = set(x.strip() for x in line.split(':', 1)[1].split(','))
            elif line.startswith('Alphabet:'):
                alphabet = set(x.strip() for x in line.split(':', 1)[1].split(','))
            elif line.startswith('Start:'):
                start = line.split(':', 1)[1].strip()
            elif line.startswith('Accept:'):
                accept = set(x.strip() for x in line.split(':', 1)[1].split(','))
            elif line.startswith('Transitions:'):
                section = 'trans'
            elif section == 'trans':
                left, right = line.split('->')
                s, sym = (x.strip() for x in left.split(','))
                dests = [x.strip() for x in right.split(',') if x.strip()]
                transitions[(s, sym)] = set(dests)
        return NFA(states, alphabet, transitions, start, accept)


def epsilon_closure(nfa: NFA, state_set: set) -> set:
    stack, closure = list(state_set), set(state_set)
    while stack:
        s = stack.pop()
        for nxt in nfa.transitions.get((s, ''), []):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure


def move(nfa: NFA, state_set: set, symbol: str) -> set:
    result = set()
    for s in state_set:
        result |= nfa.transitions.get((s, symbol), set()) # Union Operator
    return result


def nfa_to_dfa(nfa: NFA):
    dfa_states, dfa_trans, dfa_accept = set(), {}, set()
    alpha = nfa.alphabet.copy()
    start = frozenset(epsilon_closure(nfa, {nfa.start_state}))
    queue = deque([start])
    dfa_states.add(start)
    if nfa.accept_states & set(start): 
        dfa_accept.add(start)

    logs = []

    while queue:
        curr = queue.popleft()
        logs.append(f"Current DFA state: {sorted(curr)}")
        for sym in alpha:
            mv = move(nfa, curr, sym)
            nxt = frozenset(epsilon_closure(nfa, mv))
            dfa_trans[(curr, sym)] = nxt
            logs.append(f"  On '{sym}': move -> {sorted(mv)}, ε-closure -> {sorted(nxt)}")
            if nxt not in dfa_states:
                dfa_states.add(nxt)
                queue.append(nxt)
                if nfa.accept_states & set(nxt):
                    dfa_accept.add(nxt)
    return dfa_states, alpha, dfa_trans, start, dfa_accept, logs




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
        format='svg',
        graph_attr=
        {'rankdir': 'LR', 
         'nodesep': '0.5', 
         'ranksep': '0.75'},
        node_attr=
        {'fontname': font},
        edge_attr=
        {'fontname': font}
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
    return dot

# ------------------------
# Streamlit Web UI
# ------------------------

st.set_page_config(page_title="NFA to DFA Converter", layout="wide")
st.title("🧠 NFA to DFA 可视化工具")

# Persistent state
if "page" not in st.session_state:
    st.session_state.page = 0
if "dfa_result" not in st.session_state:
    st.session_state.dfa_result = None

# 页面 0：介绍页面
if st.session_state.page == 0:
    st.subheader("🚀 欢迎使用 NFA 转换 DFA 可视化工具")
    st.markdown("""
本工具支持：
- 基于文本格式输入一个 NFA
- 自动转换为等价的 DFA
- 可视化查看状态转换图

点击下方按钮开始！
""")
    if st.button("➡️ 开始输入 NFA"):
        st.session_state.page = 1

# 页面 1：输入 NFA
if st.session_state.page >= 1:
    st.header("✍️ 输入 NFA 描述文本")
    default_example = """States: 0,1,2,3,4,5,6,7,8,9,10
Alphabet: a,b
Start: 0
Accept: 10
Transitions:
0,->1,7
1,->2,4
2,a->3
3,->6
4,b->5
5,->6
6,->1,7
7,a->8
8,b->9
9,b->10
"""
    text_input = st.text_area("输入 NFA 格式", value=default_example, height=300)

    if st.button("✅ 转换为 DFA"):
        try:
            nfa = NFA.parse_from_text(text_input)
            dfa_states, alpha, dfa_trans, dfa_start, dfa_accept, logs = nfa_to_dfa(nfa)
            st.session_state.dfa_result = {
                "nfa": nfa,
                "dfa_states": dfa_states,
                "dfa_trans": dfa_trans,
                "dfa_start": dfa_start,
                "dfa_accept": dfa_accept,
                "logs": logs,
            }
            st.session_state.page = 2
        except Exception as e:
            st.error(f"解析失败：{e}")

# 页面 2：展示结果
if st.session_state.page == 2:
    st.header("📊 NFA & DFA 可视化")

    with st.expander("🔍 NFA 图像",expanded=1):
        dot_nfa = visualize_automaton(
            st.session_state.dfa_result["nfa"].states,
            st.session_state.dfa_result["nfa"].transitions,
            st.session_state.dfa_result["nfa"].start_state,
            st.session_state.dfa_result["nfa"].accept_states,
            title="NFA"
        )
        st.graphviz_chart(dot_nfa)

    with st.expander("🔁 DFA 图像",expanded=1):
        dot_dfa = visualize_automaton(
            st.session_state.dfa_result["dfa_states"],
            st.session_state.dfa_result["dfa_trans"],
            st.session_state.dfa_result["dfa_start"],
            st.session_state.dfa_result["dfa_accept"],
            title="DFA"
        )
        st.graphviz_chart(dot_dfa)
    if st.session_state.dfa_result["logs"]:
        with st.expander("📝 转换过程日志",expanded=1):
            for log in st.session_state.dfa_result["logs"]:
                st.write(log)

    if st.button("🔙 返回编辑"):
        st.session_state.page = 1
