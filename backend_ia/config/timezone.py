'''
Módulo central de gerenciamento de timezone para o projeto DAM.
Padroniza todas as operações de data/hora no Fuso Horário Oficial de Brasília (UTC-3).
Evita divergências causadas por containers/servidores executando com relógio em UTC.
'''

from datetime import datetime, timezone, timedelta

# Fuso horário oficial de Brasília (UTC-3)
TZ_BRASILIA = timezone(timedelta(hours=-3))


def get_brasilia_now() -> datetime:
    '''Retorna o datetime atual explicitamente no fuso de Brasília (UTC-3).'''
    return datetime.now(TZ_BRASILIA)


def get_brasilia_now_naive() -> datetime:
    '''Retorna o datetime atual em Brasília sem tzinfo (para compatibilidade com libs legadas e comparações ingênuas).'''
    return get_brasilia_now().replace(tzinfo=None)


def get_brasilia_now_str(fmt: str = "%Y-%m-%d %H:%M") -> str:
    '''Retorna a data e hora atual em Brasília formatada como string.'''
    return get_brasilia_now().strftime(fmt)


def to_brasilia(dt: datetime) -> datetime:
    '''Converte qualquer datetime (com ou sem tzinfo) para o fuso de Brasília.'''
    if dt is None:
        return get_brasilia_now()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ_BRASILIA)
    return dt.astimezone(TZ_BRASILIA)
