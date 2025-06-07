# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator
import re

class LanguageDetectionConfig(BaseModel):
    min_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    allowed_languages: List[str] = Field(default=["en"])
    mixed_language_threshold: float = Field(ge=0.0, le=1.0, default=0.2)

class CorruptionDetectionConfig(BaseModel):
    non_printable_ratio_threshold: float = Field(ge=0.0, le=1.0, default=0.1)
    long_run_threshold: int = Field(gt=0, default=50)
    word_diversity_threshold: float = Field(ge=0.0, le=1.0, default=0.3)
    symbol_ratio_threshold: float = Field(ge=0.0, le=1.0, default=0.4)
    known_corruption_markers: List[str] = Field(default=[
        "",
        "\\u0000",
        "\\ufffd",
        "\\x00"
    ])

class QualityMetricsConfig(BaseModel):
    min_tokens: int = Field(gt=0, default=100)
    max_tokens: int = Field(gt=0, default=1000000)
    min_sentence_length: int = Field(gt=0, default=3)
    max_sentence_length: int = Field(gt=0, default=100)
    min_word_length: int = Field(gt=0, default=2)
    max_word_length: int = Field(gt=0, default=50)

    @validator('max_tokens')
    def max_tokens_greater_than_min(cls, v, values):
        if 'min_tokens' in values and v <= values['min_tokens']:
            raise ValueError('max_tokens must be greater than min_tokens')
        return v

    @validator('max_sentence_length')
    def max_sentence_greater_than_min(cls, v, values):
        if 'min_sentence_length' in values and v <= values['min_sentence_length']:
            raise ValueError('max_sentence_length must be greater than min_sentence_length')
        return v

    @validator('max_word_length')
    def max_word_greater_than_min(cls, v, values):
        if 'min_word_length' in values and v <= values['min_word_length']:
            raise ValueError('max_word_length must be greater than min_word_length')
        return v

class DomainClassificationConfig(BaseModel):
    min_confidence: float = Field(ge=0.0, le=1.0, default=0.6)
    required_keywords: List[str] = Field(default=[
        "crypto", "blockchain", "bitcoin", "ethereum", "defi",
        "token", "mining", "wallet", "exchange", "smart contract"
    ])
    optional_keywords: List[str] = Field(default=[
        "finance", "trading", "investment", "market", "price",
        "asset", "security", "regulation", "technology", "innovation"
    ])

class TableDetectionConfig(BaseModel):
    min_rows: int = Field(gt=0, default=2)
    min_columns: int = Field(gt=0, default=2)
    max_cell_length: int = Field(gt=0, default=1000)
    table_markers: List[str] = Field(default=[
        "|", "+", "-", "table", "row", "column"
    ])

class FormulaDetectionConfig(BaseModel):
    formula_markers: List[str] = Field(default=[
        "$", "\\[", "\\]", "\\(", "\\)",
        "\\begin{equation}", "\\end{equation}"
    ])

class OutputValidationConfig(BaseModel):
    required_fields: List[str] = Field(default=[
        "text", "metadata", "quality_metrics",
        "domain_classification", "language_detection",
        "corruption_detection"
    ])
    optional_fields: List[str] = Field(default=[
        "tables", "formulas", "references", "citations"
    ])

    @validator('required_fields', 'optional_fields')
    def validate_field_names(cls, v):
        # Ensure field names are valid Python identifiers
        for field in v:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
                raise ValueError(f'Invalid field name: {field}')
        return v

    @validator('optional_fields')
    def no_duplicate_fields(cls, v, values):
        if 'required_fields' in values:
            all_fields = set(values['required_fields'] + v)
            if len(all_fields) != len(values['required_fields']) + len(v):
                raise ValueError('Duplicate fields found between required and optional fields')
        return v

class QualityConfig(BaseModel):
    """Pydantic model for quality control configuration."""
    language_detection: LanguageDetectionConfig = Field(default_factory=LanguageDetectionConfig)
    corruption_detection: CorruptionDetectionConfig = Field(default_factory=CorruptionDetectionConfig)
    quality_metrics: QualityMetricsConfig = Field(default_factory=QualityMetricsConfig)
    domain_classification: DomainClassificationConfig = Field(default_factory=DomainClassificationConfig)
    table_detection: TableDetectionConfig = Field(default_factory=TableDetectionConfig)
    formula_detection: FormulaDetectionConfig = Field(default_factory=FormulaDetectionConfig)
    output_validation: OutputValidationConfig = Field(default_factory=OutputValidationConfig)

    class Config:
        json_schema_extra = {
            "example": {
                "language_detection": {
                    "min_confidence": 0.8,
                    "allowed_languages": ["en"],
                    "mixed_language_threshold": 0.2
                }
            }
        } 