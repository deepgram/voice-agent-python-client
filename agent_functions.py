
def pick_author(author="Charles Dickens"):
    return f"Tell a story in the same style as {author}.  If you don't know the author, say 'I don't know who that is.'"

def end_story():
    return "good-bye"

FUNCTION_MAP = {
    "pick_author": pick_author,
    "end_story": end_story

}