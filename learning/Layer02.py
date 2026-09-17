from langchain_text_splitters import RecursiveCharacterTextSplitter

with open("knowledge.md", "r") as f:
    doc = f.read()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""],
)

chunks = splitter.split_text(doc)

print(f"切成了 {len(chunks)} 块\n")
for i, chunk in enumerate(chunks):
    print(f"===== 第 {i+1} 块（{len(chunk)} 字）=====")
    print(chunk[:80])
    print()