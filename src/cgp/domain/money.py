import re


class MoneyError(ValueError):
    pass


def parse_amount(value):
    if isinstance(value, bool):
        raise MoneyError("Informe um valor monetário válido.")
    if isinstance(value, int):
        cents = value
        if cents <= 0:
            raise MoneyError("O valor deve ser maior que zero.")
        return cents
    if not isinstance(value, str):
        raise MoneyError("Informe um valor monetário válido.")
    text = value.strip().replace("R$", "").replace("\u00a0", "").replace(" ", "")
    if not text or text.startswith(("-", "+")):
        raise MoneyError("Informe um valor monetário positivo.")
    if "," in text and "." in text:
        decimal_separator = "," if text.rfind(",") > text.rfind(".") else "."
        grouping_separator = "." if decimal_separator == "," else ","
        integer, fraction = text.rsplit(decimal_separator, 1)
        groups = integer.split(grouping_separator)
        if len(groups) > 1 and (not groups[0].isdigit() or not 1 <= len(groups[0]) <= 3 or any(len(group) != 3 or not group.isdigit() for group in groups[1:])):
            raise MoneyError("Informe um valor monetário válido.")
        integer = "".join(groups)
    elif "," in text:
        integer, fraction = text.rsplit(",", 1)
        if not integer.isdigit():
            raise MoneyError("Informe um valor monetário válido.")
    elif "." in text:
        groups = text.split(".")
        if len(groups) > 2 and groups[0].isdigit() and 1 <= len(groups[0]) <= 3 and all(group.isdigit() and len(group) == 3 for group in groups[1:]):
            integer = "".join(groups)
            fraction = ""
        elif len(groups) == 2 and groups[0].isdigit() and groups[1].isdigit() and len(groups[1]) == 3 and len(groups[0]) <= 3:
            integer = "".join(groups)
            fraction = ""
        elif len(groups) == 2:
            integer, fraction = groups
        else:
            raise MoneyError("Informe um valor monetário válido.")
    else:
        integer, fraction = text, ""
    if not integer.isdigit() or (fraction and not re.fullmatch(r"\d{1,2}", fraction)):
        raise MoneyError("Use até duas casas decimais no valor.")
    cents = int(integer) * 100 + int(fraction.ljust(2, "0") or "0")
    if cents <= 0:
        raise MoneyError("O valor deve ser maior que zero.")
    return cents


def format_brl(cents):
    if isinstance(cents, bool) or not isinstance(cents, int):
        raise MoneyError("O valor interno deve ser expresso em centavos inteiros.")
    sign = "-" if cents < 0 else ""
    whole, fraction = divmod(abs(cents), 100)
    grouped = f"{whole:,}".replace(",", ".")
    return f"{sign}R$ {grouped},{fraction:02d}"
