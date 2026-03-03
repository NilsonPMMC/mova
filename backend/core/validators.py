# Core validators
from django.core.exceptions import ValidationError
import re


def validate_cpf(value: str) -> str:
    """
    Valida CPF pelo algoritmo dos dígitos verificadores (módulo 11).
    Retorna o CPF apenas com dígitos (11 caracteres) se válido.
    Levanta ValidationError com mensagem explícita se inválido.
    """
    if not value or not isinstance(value, str):
        raise ValidationError("CPF inválido. Verifique os números.")

    cpf = re.sub(r"[^\d]", "", value.strip())

    if len(cpf) != 11:
        raise ValidationError("CPF inválido. Verifique os números.")

    # Rejeita sequências óbvias (todos iguais)
    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido. Verifique os números.")

    # Primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    if int(cpf[9]) != d1:
        raise ValidationError("CPF inválido. Verifique os números.")

    # Segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    if int(cpf[10]) != d2:
        raise ValidationError("CPF inválido. Verifique os números.")

    return cpf
