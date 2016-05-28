def chunker(seq, size):
    """Splits a given sequence 'seq' into chunks of size 'size'.

    Args:
      seq (list): Sequence to be split up
      size (int): Size of the chunks

    Returns:
      Generator
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def show_progress(current_value, max_value, text, end=False):
    percentage = int((current_value/max_value)*100)
    progress = "\r[{0}{1}] {2} | {3}% | {4}{5}".format(
        "=" * (percentage//5),
        " " * (20-percentage//5),
        "{0}/{1}".format(current_value, max_value),
        percentage,
        text,
        "\n" if end else ""
    )
    print(progress, end="")
