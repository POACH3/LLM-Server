# Builds one prompt for tests/long-document-test, cut so that the model
# reads exactly TOKENS tokens when it is sent as one chat message (the
# message plus the model's chat format, the count the server reports). Run
# with oMLX's Python, which loads each tokenizer the way oMLX does; it reads
# only local files.
#
#   python build-long-prompt.py build MODEL-DIR KIND TOKENS RUN-ID PROSE-FILE CODE-DIR
#
# Prints JSON: the prompt, its token count, and two questions with their
# expected answers. KIND is "prose" or "code". The two answers are invented
# facts placed about a quarter and three quarters of the way in, so a model
# can only know them by reading the prompt.

import json
import os
import sys

# Offline only: never contact Hugging Face.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Invented facts, written to sit naturally in each kind of text.
PROSE_FACTS = [
    ("Captain Leclère, it was said in Marseilles, kept aboard the Pharaon a tame "
     "grey heron which the sailors had named Pistachio, and which would eat only "
     "sardines from Toulon.",
     "In the text, what was the name of the tame heron kept aboard the Pharaon?",
     "Pistachio"),
    ("The old innkeeper at Beaucaire kept his best wine, a dark red he called "
     "Lune Amère, in a cellar beneath a well whose stones he had painted turquoise.",
     "In the text, what colour had the innkeeper at Beaucaire painted the stones "
     "of his well?",
     "turquoise"),
]
CODE_FACTS = [
    ("harborlights/ledger.py",
     "def reconcile_lantern_tallies(ledger, nightly_counts):\n"
     "    \"\"\"Match each lantern's nightly count against the harbour ledger.\"\"\"\n"
     "    return {name: ledger.get(name, 0) - count\n"
     "            for name, count in nightly_counts.items()}\n",
     "Which file in the text defines the function `reconcile_lantern_tallies`? "
     "Answer with the file name.",
     "ledger.py"),
    ("quillworks/stamps.py",
     "def emboss_wax_seal(letter, crest, temperature=82):\n"
     "    \"\"\"Return the letter with the crest pressed into warm wax.\"\"\"\n"
     "    return letter + '\\n[seal: %s at %d C]' % (crest, temperature)\n",
     "Which file in the text defines the function `emboss_wax_seal`? "
     "Answer with the file name.",
     "stamps.py"),
]


def tokenizer(model_dir):
    # Loaded exactly as oMLX loads it, with oMLX's own model-specific fixes
    # (for example Laguna's corrected splitting pattern), so the counts here
    # match what the server counts.
    from transformers import AutoTokenizer
    from omlx.utils.tokenizer import get_tokenizer_config
    return AutoTokenizer.from_pretrained(model_dir, local_files_only=True,
                                         **get_tokenizer_config(model_dir))


def count(tok, text):
    # Tokens in the text alone.
    return len(tok(text, add_special_tokens=False)["input_ids"])


def count_as_message(tok, text):
    # Tokens the model reads when the text is sent as one chat message: the
    # text plus the chat format around it. This is what the server reports.
    # Done as oMLX does it: the chat is rendered to text, then turned into
    # tokens with the tokenizer's defaults, which for some models (Laguna)
    # adds a start-of-text token on top of the one in the chat format.
    rendered = tok.apply_chat_template([{"role": "user", "content": text}], tokenize=False,
                                       add_generation_prompt=True)
    return len(tok.encode(rendered))


def prose_source(path, chars):
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    # Only the book itself, without Project Gutenberg's front and back matter.
    start = text.index("\n", text.index("*** START OF")) + 1
    end = text.index("*** END OF")
    return text[start:end].strip()[:chars]


def code_source(root, chars):
    # This Mac's Python standard library: top-level files, then one level of
    # folders, in alphabetical order, each under a heading naming the file.
    names = sorted(n for n in os.listdir(root) if n.endswith(".py"))
    names += sorted(os.path.join(d, n) for d in sorted(os.listdir(root))
                    if os.path.isdir(os.path.join(root, d))
                    for n in os.listdir(os.path.join(root, d)) if n.endswith(".py"))
    out, total = [], 0
    for name in names:
        try:
            with open(os.path.join(root, name), encoding="utf-8") as f:
                piece = "### File: %s\n%s\n" % (name, f.read())
        except (UnicodeDecodeError, OSError):
            continue
        out.append(piece)
        total += len(piece)
        if total >= chars:
            break
    return "".join(out)


def cut(tok, text, tokens):
    # The first `tokens` tokens of the text, cut at a token boundary.
    offsets = tok(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    if tokens >= len(offsets):
        sys.exit("The source text is shorter than %d tokens." % tokens)
    return text[:offsets[tokens - 1][1]]


def insert_prose(text, fraction, fact):
    # At the first paragraph break after the given fraction of the text.
    at = text.find("\n\n", int(len(text) * fraction))
    if at < 0:
        at = text.rfind("\n\n")
    return text[:at] + "\n\n" + fact + text[at:]


def insert_code(text, fraction, name, source):
    # Python files are long, so a file break may be far from the wanted point.
    # Insert at the nearest top-level def or class instead, and resume the
    # interrupted file under a "(continued)" heading so it still reads right.
    near = int(len(text) * fraction)
    spots = [text.find(s, near) for s in ("\ndef ", "\nclass ", "\n### File: ")]
    spots = [s for s in spots if s >= 0] or [text.rfind("\ndef ")]
    at = min(spots) + 1
    if text.startswith("### File: ", at):
        return text[:at] + "### File: %s\n%s\n" % (name, source) + text[at:]
    current = text[text.rfind("### File: ", 0, at) + 10:].split("\n", 1)[0]
    return (text[:at] + "\n### File: %s\n%s\n### File: %s (continued)\n"
            % (name, source, current) + text[at:])


def build(tok, kind, tokens, run_id, prose_file, code_dir):
    if kind == "prose":
        qa = [(q, a) for _, q, a in PROSE_FACTS]
        place = lambda body: insert_prose(insert_prose(body, 0.25, PROSE_FACTS[0][0]),
                                          0.75, PROSE_FACTS[1][0])
        extra = sum(count(tok, f) for f, _, _ in PROSE_FACTS)
        intro = "Below is the beginning of a novel."
        source = prose_source(prose_file, tokens * 8)
    else:
        qa = [(q, a) for _, _, q, a in CODE_FACTS]
        place = lambda body: insert_code(insert_code(body, 0.25, *CODE_FACTS[0][:2]),
                                         0.75, *CODE_FACTS[1][:2])
        extra = sum(count(tok, s) + 40 for _, s, _, _ in CODE_FACTS)
        intro = "Below is the source code of several Python files."
        source = code_source(code_dir, tokens * 8)
    question = "\n\nQuestion: %s" % qa[0][0]
    # Cut the source so the whole prompt lands on the exact count. Joins can
    # merge or split a token, so correct and repeat; if a cut keeps landing
    # one either side, a different blank-line pattern after the header
    # usually breaks the tie.
    for gap in ("\n\n", "\n\n\n", "\n \n"):
        header = "Test run %s.\n%s%s" % (run_id, intro, gap)
        body_tokens = tokens - count_as_message(tok, header + question) - extra
        for _ in range(10):
            prompt = header + place(cut(tok, source, body_tokens)) + question
            got = count_as_message(tok, prompt)
            if got == tokens:
                break
            body_tokens += tokens - got
        if got == tokens:
            break
    return {"prompt": prompt, "tokens": got,
            "question": qa[0][0], "answer": qa[0][1],
            "follow_up": qa[1][0], "follow_up_answer": qa[1][1]}


if __name__ == "__main__":
    tok = tokenizer(sys.argv[2])
    kind, tokens, run_id, prose_file, code_dir = sys.argv[3:8]
    json.dump(build(tok, kind, int(tokens), run_id, prose_file, code_dir), sys.stdout)
