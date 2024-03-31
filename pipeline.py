import kfp
import kfp.dsl as dsl

from kfp import compiler
from kfp.dsl import Artifact, Input, Output

@dsl.component(
    base_image="python:3.11",
    packages_to_install=[
        "langchain",
        "wikipedia"
    ]
)
def get_wikipedia_entry(concept: str, entry: Output[Artifact]):
    from langchain.utilities import WikipediaAPIWrapper

    wikipedia = WikipediaAPIWrapper()
    # The second line is the "summary" content for the first page result
    content = wikipedia.run(concept).split("\n")[1]

    with open(entry.path, "w") as file:
        file.write(content)


@dsl.component(
    base_image="python:3.11",
    packages_to_install=[
        "anthropic",
    ]
)
def translate_via_claude(
    entry: Input[Artifact],
    translation: Output[Artifact],
    language: str = "pirate style"
):
    import anthropic

    with open(entry.path, "r") as file:
        content = file.read()

    client = anthropic.Anthropic(
        api_key="YOUR KEY HERE",
    )

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"Rewrite the following text in {language}:\n\n{content}"}
        ]
    )

    with open(translation.path, "w") as file:
        file.write(message.content[0].text)


@dsl.pipeline(
    name="claude-pipeline"
)
def claude_pipeline(concept: str):
    get_wikipedia_entry_task = get_wikipedia_entry(
        concept=concept
    )
    translate_via_claude_task = translate_via_claude(
        entry=get_wikipedia_entry_task.outputs["entry"]
    )

compiler.Compiler().compile(claude_pipeline, "pipeline.json")