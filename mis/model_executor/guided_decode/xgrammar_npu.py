# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import json
import re
from dataclasses import dataclass, field
from typing import List, Union

import torch
from transformers import PreTrainedTokenizerBase
from vllm.config import ModelConfig
from vllm.sampling_params import GuidedDecodingParams
from vllm.transformers_utils.tokenizers.mistral import MistralTokenizer

import mis.envs as envs
from mis.logger import init_logger

xgr_installed = True
try:
    import xgrammar as xgr
    from xgrammar.base import _core as xgr_core
    from xgrammar import TokenizerInfo
except ImportError:
    xgr_installed = False

if (envs.MIS_GUIDED_DECODE_BACKEND == "npu" or
        envs.MIS_GUIDED_DECODE_BACKEND == "xgrammar_npu" or
        envs.MIS_GUIDED_DECODE_BACKEND == "xgrammar_cpu"):
    enable_mis_xgrammar = True
else:
    enable_mis_xgrammar = False

logger = init_logger(__name__)

INT_SIZE = 32


async def get_local_xgrammar_npu_guided_decoding_logits_processor(
        guided_params: GuidedDecodingParams,
        tokenizer: PreTrainedTokenizerBase,
        model_config: ModelConfig,
        max_threads: int = 8):
    """
    This is an external interface for vllm.
    Parse vllm parameters and initialize xgrammar_npu.
    """
    if not isinstance(guided_params, GuidedDecodingParams):
        logger.error(f"guided_params must be an instance of GuidedDecodingParams")
        raise ValueError(f"guided_params must be an instance of GuidedDecodingParams")
    if not isinstance(tokenizer, PreTrainedTokenizerBase):
        logger.error(f"tokenizer must be an instance of PreTrainedTokenizerBase")
        raise ValueError(f"tokenizer must be an instance of PreTrainedTokenizerBase")
    if not isinstance(model_config, ModelConfig):
        logger.error(f"model_config must be an instance of ModelConfig")
        raise ValueError(f"model_config must be an instance of ModelConfig")
    if not isinstance(max_threads, int):
        logger.error(f"max_threads must be an integer")
        raise ValueError(f"max_threads must be an integer")

    config = GrammarMetaConfig.from_vllm_guided_params(guided_params=guided_params,
                                                       model_config=model_config,
                                                       tokenizer=tokenizer,
                                                       max_threads=max_threads)
    return XGrammarNPULogitsProcessor(config)


def _grammar_is_lark_form(grammar: str) -> bool:
    """
    Check if grammar use Lark syntax.
    """
    if not grammar or not isinstance(grammar, str):
        return False

    for line in grammar.split('\n'):
        line = re.sub(r'(#|//).*$', '', line).strip()
        if not line:
            continue
        if '::=' in line:
            return False
    return True


class XgrTokenizerInfoNpu(TokenizerInfo):

    @classmethod
    def create_from_handle(cls, handle) -> "XgrTokenizerInfoNpu":
        """
        Construct an object of the TokenizerInfo from handle.
        """
        obj = cls.__new__(cls)
        obj.set_handle(handle)
        return obj

    def set_handle(self, handle):
        self._init_handle(handle)


@dataclass(frozen=True)
class TokenizerMetaData:
    """Metadata of tokenizer."""
    encoded_vocab: list[str] = field(default_factory=list)
    stop_token_ids: list[int] | None = None
    vocab_type: xgr.VocabType | None = None
    backend_str: str | None = None

    def __post_init__(self):
        """
        backend_str is used to create TOkenizeInfo with TokenizerInfo.from_huggingface.
        vocab_type is used within the constructor of TokenizeInfo.
        Only one of them can be set.
        """
        if self.backend_str and self.vocab_type:
            raise ValueError("Tokenizer backend_str and vocab_type are mutual exclusive,"
                             "please check.")


@dataclass
class GrammarMetaConfig:
    vocab_size: int
    tokenizer_hash: int
    json_schema: str | None = None
    grammar: str | None = None
    json_object: bool | None = None
    tokenizer_meta_data: TokenizerMetaData | None = None
    max_threads: int = 8

    @staticmethod
    def _escape_ebnf_string(s: str) -> str:
        """Escape special characters in a EBNF string."""
        return re.sub(r'(["\\])', r'\\\1', s)

    @staticmethod
    def _choice_as_grammar(choice: List[str] | None) -> str:
        if choice is None:
            raise ValueError("Choice is not set, please check.")
        escaped_choices = (GrammarMetaConfig._escape_ebnf_string(c) for c in choice)
        grammar = ('root ::= ' + ' | '.join(f'"{c}"' for c in escaped_choices))
        return grammar

    @classmethod
    def from_vllm_guided_params(cls,
                                guided_params: GuidedDecodingParams,
                                model_config: ModelConfig,
                                tokenizer: PreTrainedTokenizerBase,
                                max_threads: int = 8):
        """Parsing vllm guided decode parameters"""
        tokenizer_data = GrammarCache.get_tokenizer_meta_data(tokenizer)
        tokenizer_hash = hash(tokenizer)

        if guided_params.grammar:
            return cls._from_grammar(guided_params, model_config, tokenizer_hash, tokenizer_data, max_threads)
        elif guided_params.json:
            return cls._from_json(guided_params, model_config, tokenizer_hash, tokenizer_data, max_threads)
        elif guided_params.json_object:
            return cls._from_json_object(model_config, tokenizer_hash, tokenizer_data, max_threads)
        elif guided_params.choice:
            return cls._from_choice(guided_params, model_config, tokenizer_hash, tokenizer_data, max_threads)
        else:
            raise ValueError("Not supported grammar mode for xgrammar!")


    @classmethod
    def _from_grammar(cls, guided_params, model_config, tokenizer_hash, tokenizer_data, max_threads):
        if _grammar_is_lark_form(guided_params.grammar):
            raise ValueError("XGrammar only support GBNF grammars, current"
                             "grammar seems to be lark form.")
        grammar = guided_params.grammar
        try:
            xgr.Grammar.from_ebnf(grammar)
        except RuntimeError as err:
            raise ValueError(str(err)) from err
        return cls(
                   vocab_size=model_config.hf_text_config.vocab_size,
                   tokenizer_hash=tokenizer_hash,
                   max_threads=max_threads,
                   tokenizer_meta_data=tokenizer_data)

    @classmethod
    def _from_json(cls, guided_params, model_config, tokenizer_hash, tokenizer_data, max_threads):
        json_schema = json.dumps(guided_params.json) if not isinstance(guided_params.json, str) else guided_params.json
        try:
            xgr.Grammar.from_json_schema(json_schema)
        except RuntimeError as err:
            raise ValueError(str(err)) from err
        return cls(json_schema=json_schema,
                   vocab_size=model_config.hf_text_config.vocab_size,
                   tokenizer_hash=tokenizer_hash,
                   max_threads=max_threads,
                   tokenizer_meta_data=tokenizer_data)

    @classmethod
    def _from_json_object(cls, model_config, tokenizer_hash, tokenizer_data, max_threads):
        return cls(json_object=True,
                   vocab_size=model_config.hf_text_config.vocab_size,
                   tokenizer_hash=tokenizer_hash,
                   max_threads=max_threads,
                   tokenizer_meta_data=tokenizer_data)

    @classmethod
    def _from_choice(cls, guided_params, model_config, tokenizer_hash, tokenizer_data, max_threads):
        choice_str = GrammarMetaConfig._choice_as_grammar(guided_params.choice)
        return cls(
                   vocab_size=model_config.hf_text_config.vocab_size,
                   tokenizer_hash=tokenizer_hash,
                   max_threads=max_threads,
                   tokenizer_meta_data=tokenizer_data)

    def from_mindie_guided_params(self):
        """
        This interface is reserved.
        It is implemented based on the post-processing process when the new framework is connected.
        """
        raise NotImplementedError("The current interface is not implemented."
                                  " It is a reserved interface!")


class GrammarCache:
    """
    Cache for tokenizer data and xgrammar compiler.

    Avoid the repeated processing of same tokenizer.
    Reduce resource usage for creating new compiler instances with the
    same tokenizer configuration.
    """
    tokenizer_cache: dict[int, TokenizerMetaData] = {}
    compiler_cache: dict[str, xgr.GrammarCompiler] = {}

    @classmethod
    def get_compiler(cls, config: GrammarMetaConfig) -> xgr.GrammarCompiler:
        """
        This func will searches for a match GrammarCompiler from the cache first.
        If no match is found, will create a new compiler then save in the cache.

        Return a xgr.GrammarCompiler based on input config.
        """
        cache_key = str(config.tokenizer_hash)
        if cache_key not in cls.compiler_cache:
            if config.tokenizer_meta_data is None or config.tokenizer_meta_data.encoded_vocab is None:
                raise ValueError("Mising tokenizer vocab, please check.")

            config_tokenizer_data = config.tokenizer_meta_data
            # toklenizer type is PreTrainedTokenizerBase
            if config_tokenizer_data.backend_str:
                tokenizer_info = XgrTokenizerInfoNpu.create_from_handle(
                    xgr_core.TokenizerInfo.from_huggingface(
                        config_tokenizer_data.encoded_vocab,
                        config_tokenizer_data.backend_str,
                        config.vocab_size,
                        config_tokenizer_data.stop_token_ids))

            # toklenizer type is  MistralTokenizer
            else:
                tokenizer_info = xgr.TokenizerInfo(
                    config_tokenizer_data.encoded_vocab,
                    config_tokenizer_data.vocab_type,
                    vocab_size=config.vocab_size,
                    stop_token_ids=config_tokenizer_data.stop_token_ids)
            # Instantiate GrammarCompiler and store it in the dictionary.
            cls.compiler_cache[cache_key] = xgr.GrammarCompiler(
                tokenizer_info, max_threads=config.max_threads)

        return cls.compiler_cache[cache_key]

    @classmethod
    def get_tokenizer_meta_data(cls, tokenizer: PreTrainedTokenizerBase) -> TokenizerMetaData:
        """
        This func will searches for a match tokenizer data from the cache first.
        If no match is found, will create a new meta data then save in the cache.

        Return a meta data based on input tokenizer.
        """
        tokenizer_hash = hash(tokenizer)
        if tokenizer_hash not in cls.tokenizer_cache:
            try:
                encoded_vocab = [token for token, _ in sorted(tokenizer.get_vocab().items(), key=lambda x: x[1])]
            except AttributeError as e:
                raise ValueError(
                    f"Cannot get the vocabulary of the tokenizer {type(tokenizer)}."
                    f"The tokenizer should have a get_vocab method.") from e

            stop_token_ids = None
            # Obtain eos_token_id from tokenizer
            if stop_token_ids is None and hasattr(tokenizer, "eos_token_id") \
                    and tokenizer.eos_token_id is not None:
                stop_token_ids = [tokenizer.eos_token_id]

            backend_str = ""
            vocab_type = xgr.VocabType.RAW
            # Obtain backend_str from PreTrainedTokenizerBase
            if isinstance(tokenizer, PreTrainedTokenizerBase):
                backend_str = tokenizer.backend_tokenizer.to_str()
                vocab_type = None
            # Obtain vocab_type from MistralTokenizer
            elif isinstance(tokenizer, MistralTokenizer):
                vocab_type = xgr.VocabType.BYTE_FALLBACK

            # Instantiate TokenizerMetaData and store it in the dictionary.
            cls.tokenizer_cache[tokenizer_hash] = TokenizerMetaData(
                encoded_vocab=encoded_vocab,
                stop_token_ids=stop_token_ids,
                backend_str=backend_str,
                vocab_type=vocab_type)

        return cls.tokenizer_cache[tokenizer_hash]


def _apply_vocab_mask(logits: torch.Tensor, vocab_mask: torch.Tensor):
    """
    xgrammar apply mask adapted to npu device.
    """

    def stack_torch(tensors):
        row = tensors[0].shape[0]
        col = tensors[0].shape[1]
        size = len(tensors)
        return torch.stack(tensors, dim=2).reshape(row, col * size)

    def num2bit(num, idx):
        return num & (1 << idx) == 0

    vocab_mask = vocab_mask.to(device=logits.device)
    bit_masks = []

    for i in range(INT_SIZE):
        bit_masks.append(num2bit(vocab_mask, i))
    bool_mask = stack_torch(bit_masks)
    bool_mask = bool_mask.squeeze()

    logits.masked_fill_(bool_mask, float("-inf"))


@dataclass
class XGrammarNPULogitsProcessor:
    config: GrammarMetaConfig
    token_bitmask: torch.Tensor = None
    matchers: list[xgr.GrammarMatcher] = field(default_factory=list)
    context: xgr.CompiledGrammar | None = None
    batch_size: int = field(default=1)
    prefilled: bool = field(default=False)

    # overwrite function call
    def __call__(self, input_ids: tuple[Union[int, None]],
                 scores: torch.Tensor) -> torch.Tensor:
        if not (
                isinstance(input_ids, tuple) and
                all(isinstance(token_id, int) or token_id is None for token_id in input_ids)
        ):
            logger.error("input_ids must be a list of integers")
            raise ValueError("input_ids must be a list of integers")
        if not isinstance(scores, torch.Tensor):
            logger.error("scores must be a torch.Tensor")
            raise ValueError("scores must be a torch.Tensor")

        if self.context is None:
            self._initialize_ctx()

        # init matcher for each batch at the first time
        if len(self.matchers) == 0:
            self.matchers = [xgr.GrammarMatcher(self.context) for _ in range(self.batch_size)]
            self.token_bitmask = xgr.allocate_token_bitmask(
                self.batch_size, self.config.vocab_size)

        # prefill stage, skip sampled_token
        if not self.prefilled:
            # Have not sampled a token yet
            self.prefilled = True
        else:
            for i, matcher in enumerate(self.matchers):
                if not matcher.is_terminated():
                    sampled_token = input_ids[-1]
                    self.matchers[i].accept_token(sampled_token)

        # calc bit mask for each batch
        for i, matcher in enumerate(self.matchers):
            if not matcher.is_terminated():
                # parallelized with model decoding
                matcher.fill_next_token_bitmask(self.token_bitmask, i)

        if envs.MIS_GUIDED_DECODE_BACKEND == "xgrammar_cpu":
            logger.debug(f"Set xgrammar backend to cpu.")
            device_type = scores.device.type
            dtype = scores.dtype
            scores = scores.to("cpu").float().unsqueeze(0)
            xgr.apply_token_bitmask_inplace(
                scores, self.token_bitmask.to(scores.device, non_blocking=True))
            scores = scores.to(dtype).to(device_type).squeeze()
        elif envs.MIS_GUIDED_DECODE_BACKEND == "npu" or envs.MIS_GUIDED_DECODE_BACKEND == "xgrammar_npu":
            # tranform bit mask and apply bit mask to scores
            logger.debug(f"Set xgrammar backend to npu.")
            _apply_vocab_mask(scores, self.token_bitmask.to(scores.device, non_blocking=True))
        else:
            logger.warning(f"not supported xgrammar backend {envs.MIS_GUIDED_DECODE_BACKEND}, "
                           "fallback to npu.")
            _apply_vocab_mask(scores, self.token_bitmask.to(scores.device, non_blocking=True))

        return scores

    def _initialize_ctx(self):
        """
        Find the compiler of xgrammar and init context.

        Lazily initialize the processor in the worker process
        """
        if self.context is None:
            compiler = GrammarCache.get_compiler(self.config)
            if self.config.json_schema is not None:
                self.context = compiler.compile_json_schema(self.config.json_schema)
            elif self.config.grammar is not None:
                self.context = compiler.compile_grammar(self.config.grammar)
            elif self.config.json_object:
                self.context = compiler.compile_builtin_json_grammar()
            else:
                raise ValueError("Not supported grammar mode for xgrammar")
