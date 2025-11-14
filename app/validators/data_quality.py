"""Data quality validation for input features."""
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, ValidationError, validator

logger = logging.getLogger(__name__)


class DataQualityCheck(BaseModel):
    """Data quality check result."""
    
    passed: bool
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}


class CustomerFeaturesValidator:
    """
    Validate customer features for data quality.
    
    Checks include:
    - Value ranges
    - Data types
    - Missing values
    - Outliers
    - Business logic constraints
    """
    
    # Expected value ranges
    AGE_MIN = 18
    AGE_MAX = 100
    SESSIONS_MAX = 10000
    DAYS_MAX = 3650  # ~10 years
    ORDERS_MAX = 1000
    
    @staticmethod
    def validate_single(features: Dict[str, Any]) -> DataQualityCheck:
        """
        Validate a single customer record.
        
        Args:
            features: Customer features dictionary
        
        Returns:
            DataQualityCheck with validation results
        """
        errors = []
        warnings = []
        details = {}
        
        # Required fields
        required_fields = [
            "gender",
            "age",
            "bnpl_eligible",
            "number_of_sessions",
            "days_since_first_joined",
            "number_of_failed_orders",
            "number_of_successful_orders",
        ]
        
        for field in required_fields:
            if field not in features:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return DataQualityCheck(passed=False, errors=errors)
        
        # Validate gender
        gender = features.get("gender", "")
        if gender not in ["M", "F", "Unknown"]:
            warnings.append(f"Unusual gender value: {gender}")
        
        # Validate age
        age = features.get("age", 0)
        if age is not None:
            if age < 0:
                errors.append(f"Age cannot be negative: {age}")
            elif age < CustomerFeaturesValidator.AGE_MIN:
                warnings.append(f"Age below minimum ({CustomerFeaturesValidator.AGE_MIN}): {age}")
            elif age > CustomerFeaturesValidator.AGE_MAX:
                warnings.append(f"Age above maximum ({CustomerFeaturesValidator.AGE_MAX}): {age}")
        
        # Validate sessions
        sessions = features.get("number_of_sessions", 0)
        if sessions < 0:
            errors.append(f"Number of sessions cannot be negative: {sessions}")
        elif sessions > CustomerFeaturesValidator.SESSIONS_MAX:
            warnings.append(f"Unusually high number of sessions: {sessions}")
        
        # Validate days since joined
        days = features.get("days_since_first_joined", 0)
        if days < 0:
            errors.append(f"Days since joined cannot be negative: {days}")
        elif days > CustomerFeaturesValidator.DAYS_MAX:
            warnings.append(f"Days since joined is very high: {days}")
        
        # Validate orders
        failed_orders = features.get("number_of_failed_orders", 0)
        successful_orders = features.get("number_of_successful_orders", 0)
        
        if failed_orders < 0:
            errors.append(f"Failed orders cannot be negative: {failed_orders}")
        if successful_orders < 0:
            errors.append(f"Successful orders cannot be negative: {successful_orders}")
        
        if failed_orders > CustomerFeaturesValidator.ORDERS_MAX:
            warnings.append(f"Unusually high failed orders: {failed_orders}")
        if successful_orders > CustomerFeaturesValidator.ORDERS_MAX:
            warnings.append(f"Unusually high successful orders: {successful_orders}")
        
        # Business logic checks
        total_orders = failed_orders + successful_orders
        if total_orders > 0:
            failure_rate = failed_orders / total_orders
            if failure_rate > 0.5:
                warnings.append(f"High failure rate: {failure_rate:.2%}")
            details["failure_rate"] = failure_rate
        
        # Check for suspicious patterns
        if sessions == 0 and total_orders > 0:
            warnings.append("Orders without sessions is suspicious")
        
        if days == 0 and (sessions > 0 or total_orders > 0):
            warnings.append("Activity on day 0 is unusual")
        
        passed = len(errors) == 0
        
        return DataQualityCheck(
            passed=passed,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    @staticmethod
    def validate_batch(features_batch: List[Dict[str, Any]]) -> List[DataQualityCheck]:
        """
        Validate a batch of customer records.
        
        Args:
            features_batch: List of customer features
        
        Returns:
            List of DataQualityCheck results
        """
        return [
            CustomerFeaturesValidator.validate_single(features)
            for features in features_batch
        ]
    
    @staticmethod
    def validate_distribution(df: pd.DataFrame) -> DataQualityCheck:
        """
        Validate overall distribution of features.
        
        Args:
            df: DataFrame with customer features
        
        Returns:
            DataQualityCheck with distribution validation
        """
        errors = []
        warnings = []
        details = {}
        
        # Check for missing values
        missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()
        for col, pct in missing_pct.items():
            if pct > 0:
                if pct > 10:
                    errors.append(f"High missing rate in {col}: {pct:.2f}%")
                else:
                    warnings.append(f"Missing values in {col}: {pct:.2f}%")
        
        details["missing_percentages"] = missing_pct
        
        # Check for outliers (IQR method)
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            outlier_pct = outlier_count / len(df) * 100
            
            if outlier_pct > 5:
                warnings.append(f"High outlier rate in {col}: {outlier_pct:.2f}%")
            
            details[f"{col}_outliers"] = {
                "count": int(outlier_count),
                "percentage": float(outlier_pct)
            }
        
        # Check distribution skewness
        for col in numeric_cols:
            skew = df[col].skew()
            if abs(skew) > 2:
                warnings.append(f"Highly skewed distribution in {col}: {skew:.2f}")
            details[f"{col}_skewness"] = float(skew)
        
        passed = len(errors) == 0
        
        return DataQualityCheck(
            passed=passed,
            errors=errors,
            warnings=warnings,
            details=details
        )


def validate_prediction_input(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate prediction input and return cleaned version.
    
    Args:
        features: Raw customer features
    
    Returns:
        Validated and cleaned features
    
    Raises:
        ValueError: If validation fails
    """
    # Run validation
    check = CustomerFeaturesValidator.validate_single(features)
    
    # Log warnings
    for warning in check.warnings:
        logger.warning("Data quality warning: %s", warning)
    
    # Raise errors
    if not check.passed:
        error_msg = "; ".join(check.errors)
        logger.error("Data quality check failed: %s", error_msg)
        raise ValueError(f"Data validation failed: {error_msg}")
    
    return features

