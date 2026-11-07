"""Same frozen questions and two packers; explicit separate OpenAI experiment."""
from nrqa.openai_provider import OpenAI, SETTINGS, local_environment
from nrqa.providers import ProviderError
from run_api_finqa import ROOT, main


if __name__ == '__main__':
    try:
        main(lambda: OpenAI(local_environment(ROOT / '.env')), settings=SETTINGS,
             default_out=ROOT / 'artifacts/api_openai_finqa')
    except ProviderError as error:
        raise SystemExit(error.code) from None
