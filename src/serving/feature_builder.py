from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import yaml
import os
import logging

class FeatureBuilderInterface(ABC):
    """Abstract interface for building features from truncated event history."""
    
    @abstractmethod
    def build_features(self, events: pd.DataFrame, prediction_time: datetime, stay_metadata: dict) -> Dict[str, Any]:
        """Build features from events up to prediction_time.
        
        Args:
            events: DataFrame of events truncated at prediction_time
            prediction_time: The time of prediction
            stay_metadata: Dictionary of stay metadata
            
        Returns:
            Dict[str, Any]: Dictionary of constructed features
        """
        pass

class MockFeatureBuilder(FeatureBuilderInterface):
    """Mock implementation of FeatureBuilderInterface."""
    
    def __init__(self, feature_schema_path: Optional[str] = None):
        """Initialize builder and load schema.
        
        Args:
            feature_schema_path: Path to the feature schema YAML
        """
        self.num_bins = 8
        self.bin_size_hours = 6
        self.lookback_hours = 48
        
        if feature_schema_path and os.path.exists(feature_schema_path):
            try:
                with open(feature_schema_path, 'r') as f:
                    schema = yaml.safe_load(f)
                    self.num_bins = schema.get('num_bins', 8)
                    self.bin_size_hours = schema.get('bin_size_hours', 6)
                    self.lookback_hours = schema.get('lookback_hours', 48)
            except Exception as e:
                logging.warning(f"Could not load feature schema from {feature_schema_path}: {e}")

    def build_features(self, events: pd.DataFrame, prediction_time: datetime, stay_metadata: dict) -> Dict[str, Any]:
        """Build mock features.
        
        Args:
            events: Truncated events dataframe
            prediction_time: Time to predict at
            stay_metadata: Stay metadata including intime
            
        Returns:
            Dict containing features and masks
        """
        observation_mask = [0] * self.num_bins
        padding_mask = [0] * self.num_bins
        temporal_features = {}
        tslo = {}
        
        intime = stay_metadata.get('intime')
        if not isinstance(intime, datetime):
            intime = pd.to_datetime(intime).to_pydatetime()
            
        for i in range(self.num_bins):
            # Bins go backward from prediction_time
            bin_end = prediction_time - timedelta(hours=i * self.bin_size_hours)
            bin_start = bin_end - timedelta(hours=self.bin_size_hours)
            
            if bin_end > intime:
                padding_mask[i] = 1
                
            if not events.empty:
                bin_events = events[(events['event_time'] > bin_start) & (events['event_time'] <= bin_end)]
                if not bin_events.empty:
                    observation_mask[i] = 1
                    for channel in bin_events['event_name'].unique():
                        channel_events = bin_events[bin_events['event_name'] == channel]
                        if channel not in temporal_features:
                            temporal_features[channel] = [0.0] * self.num_bins
                        temporal_features[channel][i] = float(channel_events['value'].mean())
                        
                        if channel not in tslo:
                            tslo[channel] = [-1.0] * self.num_bins
                        
                        last_time = channel_events['event_time'].max()
                        tslo[channel][i] = (prediction_time - last_time).total_seconds() / 3600.0

        # Backfill TSLO where needed
        for channel in temporal_features:
            if channel not in tslo:
                tslo[channel] = [-1.0] * self.num_bins
            else:
                for i in range(self.num_bins):
                    if tslo[channel][i] == -1.0 and observation_mask[i] == 0:
                        last_val = tslo[channel][i-1] if i > 0 else -1.0
                        if last_val != -1.0:
                            tslo[channel][i] = last_val + self.bin_size_hours
                            
        observed_bins = sum(observation_mask)
        
        static_features = {
            'age': stay_metadata.get('age', 65),
            'sex': stay_metadata.get('sex', 'M')
        }
        
        return {
            'temporal_features': temporal_features,
            'observation_mask': observation_mask,
            'padding_mask': padding_mask,
            'tslo': tslo,
            'static_features': static_features,
            'observed_bins': observed_bins,
            'total_bins': self.num_bins,
            'prediction_time': prediction_time,
            'lookback_hours': self.lookback_hours
        }
