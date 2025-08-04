"""
Signal Scanner API

This module provides a Flask API for managing signal configurations and viewing generated signals.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus as urlquote
from marshmallow import Schema, fields, validate, ValidationError
from flask_caching import Cache

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database models
from backend.app.signal_scanner.db_schema import (
    SignalConfig, SignalSymbol, SignalEntryRule, SignalExitRule,
    GeneratedSignal, SignalCondition, Base
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Set up JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change in production
jwt = JWTManager(app)

# Set up rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Add specific rate limits for different endpoints
limiter.limit("100 per hour")(app.route('/api/signal-configs', methods=['GET']))
limiter.limit("50 per hour")(app.route('/api/signal-configs', methods=['POST']))
limiter.limit("50 per hour")(app.route('/api/signal-configs/<int:config_id>', methods=['PUT']))
limiter.limit("20 per hour")(app.route('/api/signal-configs/<int:config_id>', methods=['DELETE']))
limiter.limit("100 per hour")(app.route('/api/signals', methods=['GET']))

# Add caching
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
})

# Database connection
password = os.getenv("DB_PASSWORD", "password")
encoded_password = urlquote(password)
uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@100.121.186.86:5432/theodb")
engine = create_engine(uri)
Session = sessionmaker(bind=engine)

# Ensure tables exist
Base.metadata.create_all(engine)

# Validation schemas
class SignalSymbolSchema(Schema):
    symbol = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    token = fields.Int(allow_none=True)
    is_primary = fields.Bool(default=False)
    timeframe = fields.Str(validate=validate.OneOf(['5min', '15min', '30min', '1h']), default='15min')
    weight = fields.Float(validate=validate.Range(min=0.0, max=1.0), default=1.0)

class SignalEntryRuleSchema(Schema):
    rule_type = fields.Str(required=True, validate=validate.OneOf([
        'PriceAbove', 'PriceBelow', 'CrossAbove', 'CrossBelow',
        'Correlation', 'RSI', 'MACD', 'Custom'
    ]))
    symbol = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    parameter = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    value = fields.Float(allow_none=True)
    comparison = fields.Str(validate=validate.OneOf(['>', '<', '==', '>=', '<=']), allow_none=True)
    timeframe = fields.Str(validate=validate.OneOf(['5min', '15min', '30min', '1h']), default='15min')
    is_required = fields.Bool(default=True)
    correlated_symbol = fields.Str(validate=validate.Length(min=1, max=20), allow_none=True)
    correlation_lookback = fields.Int(validate=validate.Range(min=1, max=100), default=10)
    correlation_threshold = fields.Float(validate=validate.Range(min=0.0, max=1.0), default=0.7)

class SignalExitRuleSchema(Schema):
    rule_type = fields.Str(required=True, validate=validate.OneOf([
        'PriceAbove', 'PriceBelow', 'CrossAbove', 'CrossBelow',
        'Correlation', 'RSI', 'MACD', 'TimeElapsed', 'Custom'
    ]))
    symbol = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    parameter = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    value = fields.Float(allow_none=True)
    comparison = fields.Str(validate=validate.OneOf(['>', '<', '==', '>=', '<=']), allow_none=True)
    timeframe = fields.Str(validate=validate.OneOf(['5min', '15min', '30min', '1h']), default='15min')
    priority = fields.Int(validate=validate.Range(min=1, max=10), default=1)
    minutes_elapsed = fields.Int(validate=validate.Range(min=1), allow_none=True)

class SignalConfigSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=500), allow_none=True)
    signal_type = fields.Str(required=True, validate=validate.OneOf(['Intraday', 'Positional']))
    expiry = fields.Str(required=True, validate=validate.OneOf(['Daily', 'Weekly', 'Monthly']))
    trading_days = fields.Str(validate=validate.Regexp(r'^(Mon|Tue|Wed|Thu|Fri)(,(Mon|Tue|Wed|Thu|Fri))*$'), default='Mon,Tue,Wed,Thu,Fri')
    start_time = fields.Str(validate=validate.Regexp(r'^([01]\d|2[0-3]):([0-5]\d)$'), default='09:30')
    end_time = fields.Str(validate=validate.Regexp(r'^([01]\d|2[0-3]):([0-5]\d)$'), default='16:00')
    scan_interval_minutes = fields.Int(validate=validate.Range(min=1, max=60), default=15)
    max_signals_per_day = fields.Int(validate=validate.Range(min=1, max=100), default=5)
    signal_direction = fields.Str(validate=validate.OneOf(['Long', 'Short', 'Both']), default='Both')
    instrument_type = fields.Str(validate=validate.OneOf(['Stock', 'Option', 'Future', 'ETF']), default='Stock')
    option_type = fields.Str(validate=validate.OneOf(['CALL', 'PUT', 'Both']), default='Both')
    option_category = fields.Str(validate=validate.OneOf(['ITM', 'OTM', 'ATM', 'DITM', 'DOTM', 'Any']), default='Any')
    mode = fields.Str(validate=validate.OneOf(['Live', 'Virtual', 'Backtest']), default='Virtual')
    is_active = fields.Bool(default=True)
    symbols = fields.Nested(SignalSymbolSchema, many=True, required=True)
    entry_rules = fields.Nested(SignalEntryRuleSchema, many=True, required=True)
    exit_rules = fields.Nested(SignalExitRuleSchema, many=True, required=True)

# Initialize schemas
signal_config_schema = SignalConfigSchema()
signal_symbol_schema = SignalSymbolSchema()
signal_entry_rule_schema = SignalEntryRuleSchema()
signal_exit_rule_schema = SignalExitRuleSchema()

@app.route('/api/signal-configs', methods=['GET'])
@jwt_required()
def get_signal_configs():
    """Get all signal configurations."""
    session = Session()
    try:
        configs = session.query(SignalConfig).all()
        result = []
        for config in configs:
            config_dict = {
                'id': config.id,
                'name': config.name,
                'description': config.description,
                'signal_type': config.signal_type,
                'expiry': config.expiry,
                'trading_days': config.trading_days,
                'start_time': config.start_time,
                'end_time': config.end_time,
                'scan_interval_minutes': config.scan_interval_minutes,
                'max_signals_per_day': config.max_signals_per_day,
                'signal_direction': config.signal_direction,
                'instrument_type': config.instrument_type,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None
            }
            result.append(config_dict)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting signal configurations: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/signal-configs/<int:config_id>', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_signal_config(config_id):
    """Get a specific signal configuration with its symbols and rules."""
    session = Session()
    try:
        config = session.query(SignalConfig).filter(SignalConfig.id == config_id).first()
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Get symbols
        symbols = session.query(SignalSymbol).filter(SignalSymbol.config_id == config_id).all()
        symbols_list = []
        for symbol in symbols:
            symbols_list.append({
                'id': symbol.id,
                'symbol': symbol.symbol,
                'token': symbol.token,
                'is_primary': symbol.is_primary,
                'timeframe': symbol.timeframe,
                'weight': symbol.weight
            })
        
        # Get entry rules
        entry_rules = session.query(SignalEntryRule).filter(SignalEntryRule.config_id == config_id).all()
        entry_rules_list = []
        for rule in entry_rules:
            entry_rules_list.append({
                'id': rule.id,
                'rule_type': rule.rule_type,
                'symbol': rule.symbol,
                'parameter': rule.parameter,
                'value': rule.value,
                'comparison': rule.comparison,
                'timeframe': rule.timeframe,
                'is_required': rule.is_required,
                'correlated_symbol': rule.correlated_symbol,
                'correlation_lookback': rule.correlation_lookback,
                'correlation_threshold': rule.correlation_threshold
            })
        
        # Get exit rules
        exit_rules = session.query(SignalExitRule).filter(SignalExitRule.config_id == config_id).all()
        exit_rules_list = []
        for rule in exit_rules:
            exit_rules_list.append({
                'id': rule.id,
                'rule_type': rule.rule_type,
                'symbol': rule.symbol,
                'parameter': rule.parameter,
                'value': rule.value,
                'comparison': rule.comparison,
                'timeframe': rule.timeframe,
                'priority': rule.priority,
                'minutes_elapsed': rule.minutes_elapsed
            })
        
        # Construct full response
        result = {
            'id': config.id,
            'name': config.name,
            'description': config.description,
            'signal_type': config.signal_type,
            'expiry': config.expiry,
            'trading_days': config.trading_days,
            'start_time': config.start_time,
            'end_time': config.end_time,
            'scan_interval_minutes': config.scan_interval_minutes,
            'max_signals_per_day': config.max_signals_per_day,
            'signal_direction': config.signal_direction,
            'instrument_type': config.instrument_type,
            'option_type': config.option_type,
            'option_category': config.option_category,
            'mode': config.mode,
            'is_active': config.is_active,
            'created_at': config.created_at.isoformat() if config.created_at else None,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            'symbols': symbols_list,
            'entry_rules': entry_rules_list,
            'exit_rules': exit_rules_list
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting signal configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/signal-configs', methods=['POST'])
@jwt_required()
@limiter.limit("50 per hour")
def create_signal_config():
    """Create a new signal configuration."""
    session = Session()
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate input data
        try:
            validated_data = signal_config_schema.load(data)
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.messages}), 400
        
        # Check for duplicate configuration name
        existing = session.query(SignalConfig).filter(SignalConfig.name == validated_data['name']).first()
        if existing:
            return jsonify({'error': 'Configuration with this name already exists'}), 409
        
        # Create config
        config = SignalConfig(
            name=validated_data['name'],
            description=validated_data.get('description'),
            signal_type=validated_data['signal_type'],
            expiry=validated_data['expiry'],
            trading_days=validated_data['trading_days'],
            start_time=validated_data['start_time'],
            end_time=validated_data['end_time'],
            scan_interval_minutes=validated_data['scan_interval_minutes'],
            max_signals_per_day=validated_data['max_signals_per_day'],
            signal_direction=validated_data['signal_direction'],
            instrument_type=validated_data['instrument_type'],
            option_type=validated_data['option_type'],
            option_category=validated_data['option_category'],
            mode=validated_data['mode'],
            is_active=validated_data['is_active']
        )
        
        session.add(config)
        session.flush()  # Get the config ID
        
        # Add symbols
        for symbol_data in validated_data['symbols']:
            symbol = SignalSymbol(
                config_id=config.id,
                symbol=symbol_data['symbol'],
                token=symbol_data.get('token'),
                is_primary=symbol_data['is_primary'],
                timeframe=symbol_data['timeframe'],
                weight=symbol_data['weight']
            )
            session.add(symbol)
        
        # Add entry rules
        for rule_data in validated_data['entry_rules']:
            rule = SignalEntryRule(
                config_id=config.id,
                rule_type=rule_data['rule_type'],
                symbol=rule_data['symbol'],
                parameter=rule_data['parameter'],
                value=rule_data.get('value'),
                comparison=rule_data.get('comparison'),
                timeframe=rule_data['timeframe'],
                is_required=rule_data['is_required'],
                correlated_symbol=rule_data.get('correlated_symbol'),
                correlation_lookback=rule_data.get('correlation_lookback'),
                correlation_threshold=rule_data.get('correlation_threshold')
            )
            session.add(rule)
        
        # Add exit rules
        for rule_data in validated_data['exit_rules']:
            rule = SignalExitRule(
                config_id=config.id,
                rule_type=rule_data['rule_type'],
                symbol=rule_data['symbol'],
                parameter=rule_data['parameter'],
                value=rule_data.get('value'),
                comparison=rule_data.get('comparison'),
                timeframe=rule_data['timeframe'],
                priority=rule_data['priority'],
                minutes_elapsed=rule_data.get('minutes_elapsed')
            )
            session.add(rule)
        
        session.commit()
        
        # Clear cache for signals endpoint
        cache.delete_memoized(get_signals)
        
        return jsonify({
            'id': config.id,
            'name': config.name,
            'message': 'Signal configuration created successfully'
        }), 201
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating signal configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()

@app.route('/api/signal-configs/<int:config_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("50 per hour")
def update_signal_config(config_id):
    """Update an existing signal configuration."""
    session = Session()
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get the config
        config = session.query(SignalConfig).filter(SignalConfig.id == config_id).first()
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # Validate input data
        try:
            validated_data = signal_config_schema.load(data)
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.messages}), 400
        
        # Update config fields
        for key, value in validated_data.items():
            if key not in ['id', 'created_at', 'updated_at', 'symbols', 'entry_rules', 'exit_rules']:
                setattr(config, key, value)
        
        # Handle symbols update if provided
        if 'symbols' in validated_data:
            # Delete existing symbols
            session.query(SignalSymbol).filter(SignalSymbol.config_id == config_id).delete()
            
            # Add new symbols
            for symbol_data in validated_data['symbols']:
                symbol = SignalSymbol(
                    config_id=config.id,
                    symbol=symbol_data['symbol'],
                    token=symbol_data.get('token'),
                    is_primary=symbol_data['is_primary'],
                    timeframe=symbol_data['timeframe'],
                    weight=symbol_data['weight']
                )
                session.add(symbol)
        
        # Handle entry rules update if provided
        if 'entry_rules' in validated_data:
            # Delete existing entry rules
            session.query(SignalEntryRule).filter(SignalEntryRule.config_id == config_id).delete()
            
            # Add new entry rules
            for rule_data in validated_data['entry_rules']:
                rule = SignalEntryRule(
                    config_id=config.id,
                    rule_type=rule_data['rule_type'],
                    symbol=rule_data['symbol'],
                    parameter=rule_data['parameter'],
                    value=rule_data.get('value'),
                    comparison=rule_data.get('comparison'),
                    timeframe=rule_data['timeframe'],
                    is_required=rule_data['is_required'],
                    correlated_symbol=rule_data.get('correlated_symbol'),
                    correlation_lookback=rule_data.get('correlation_lookback'),
                    correlation_threshold=rule_data.get('correlation_threshold')
                )
                session.add(rule)
        
        # Handle exit rules update if provided
        if 'exit_rules' in validated_data:
            # Delete existing exit rules
            session.query(SignalExitRule).filter(SignalExitRule.config_id == config_id).delete()
            
            # Add new exit rules
            for rule_data in validated_data['exit_rules']:
                rule = SignalExitRule(
                    config_id=config.id,
                    rule_type=rule_data['rule_type'],
                    symbol=rule_data['symbol'],
                    parameter=rule_data['parameter'],
                    value=rule_data.get('value'),
                    comparison=rule_data.get('comparison'),
                    timeframe=rule_data['timeframe'],
                    priority=rule_data['priority'],
                    minutes_elapsed=rule_data.get('minutes_elapsed')
                )
                session.add(rule)
        
        session.commit()
        
        return jsonify({
            'id': config.id,
            'name': config.name,
            'message': 'Signal configuration updated successfully'
        })
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating signal configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()

@app.route('/api/signal-configs/<int:config_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("20 per hour")
def delete_signal_config(config_id):
    """Delete a signal configuration."""
    session = Session()
    try:
        config = session.query(SignalConfig).filter(SignalConfig.id == config_id).first()
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        session.delete(config)
        session.commit()
        
        return jsonify({
            'message': f'Signal configuration {config_id} deleted successfully'
        })
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting signal configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()

@app.route('/api/signals', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)  # Cache for 1 minute, vary by query parameters
def get_signals():
    """Get generated signals with optional filtering."""
    session = Session()
    try:
        # Get query parameters
        config_id = request.args.get('config_id', type=int)
        symbol = request.args.get('symbol')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Validate date formats
        try:
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            if end_date:
                end_date = datetime.fromisoformat(end_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
        
        # Validate pagination parameters
        if page < 1:
            return jsonify({'error': 'Page number must be positive'}), 400
        if per_page < 1 or per_page > 100:
            return jsonify({'error': 'Per page must be between 1 and 100'}), 400
        
        # Build query
        query = session.query(GeneratedSignal)
        
        if config_id:
            query = query.filter(GeneratedSignal.config_id == config_id)
        if symbol:
            query = query.filter(GeneratedSignal.symbol == symbol)
        if status:
            query = query.filter(GeneratedSignal.status == status)
        if start_date:
            query = query.filter(GeneratedSignal.signal_time >= start_date)
        if end_date:
            query = query.filter(GeneratedSignal.signal_time <= end_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        query = query.order_by(GeneratedSignal.signal_time.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        signals = query.all()
        
        # Format response
        result = []
        for signal in signals:
            result.append({
                'id': signal.id,
                'config_id': signal.config_id,
                'symbol': signal.symbol,
                'token': signal.token,
                'signal_time': signal.signal_time.isoformat(),
                'direction': signal.direction,
                'price': signal.price,
                'timeframe': signal.timeframe,
                'status': signal.status,
                'executed_time': signal.executed_time.isoformat() if signal.executed_time else None,
                'rejection_reason': signal.rejection_reason,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'risk_reward_ratio': signal.risk_reward_ratio
            })
        
        return jsonify({
            'signals': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting signals: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()

@app.route('/api/signals/<int:signal_id>', methods=['GET'])
@jwt_required()
def get_signal(signal_id):
    """Get a specific signal with its conditions."""
    session = Session()
    try:
        # Get the signal
        signal = session.query(GeneratedSignal).filter(GeneratedSignal.id == signal_id).first()
        if not signal:
            return jsonify({'error': 'Signal not found'}), 404
        
        # Get the config name
        config = session.query(SignalConfig).filter(SignalConfig.id == signal.config_id).first()
        config_name = config.name if config else "Unknown"
        
        # Get the conditions
        conditions = session.query(SignalCondition).filter(SignalCondition.signal_id == signal.id).all()
        conditions_list = []
        for condition in conditions:
            conditions_list.append({
                'rule_type': condition.rule_type,
                'symbol': condition.symbol,
                'parameter': condition.parameter,
                'value': condition.value,
                'comparison': condition.comparison,
                'result': condition.result
            })
        
        signal_dict = {
            'id': signal.id,
            'config_id': signal.config_id,
            'config_name': config_name,
            'symbol': signal.symbol,
            'token': signal.token,
            'signal_time': signal.signal_time.isoformat(),
            'direction': signal.direction,
            'price': signal.price,
            'timeframe': signal.timeframe,
            'status': signal.status,
            'executed_time': signal.executed_time.isoformat() if signal.executed_time else None,
            'rejection_reason': signal.rejection_reason,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'risk_reward_ratio': signal.risk_reward_ratio,
            'conditions': conditions_list
        }
        
        return jsonify(signal_dict)
    
    except Exception as e:
        logger.error(f"Error getting signal: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()

@app.route('/api/signals/<int:signal_id>/status', methods=['PUT'])
@jwt_required()
def update_signal_status(signal_id):
    """Update a signal's status."""
    session = Session()
    try:
        data = request.json
        if not data or 'status' not in data:
            return jsonify({'error': 'Status not provided'}), 400
        
        # Get the signal
        signal = session.query(GeneratedSignal).filter(GeneratedSignal.id == signal_id).first()
        if not signal:
            return jsonify({'error': 'Signal not found'}), 404
        
        # Update status
        signal.status = data['status']
        
        # Update other fields if provided
        if 'executed_time' in data and data['executed_time']:
            signal.executed_time = datetime.fromisoformat(data['executed_time'])
        elif data['status'] == 'Executed' and not signal.executed_time:
            signal.executed_time = datetime.utcnow()
        
        if 'rejection_reason' in data:
            signal.rejection_reason = data['rejection_reason']
        
        session.commit()
        
        return jsonify({
            'id': signal.id,
            'status': signal.status,
            'message': 'Signal status updated successfully'
        })
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating signal status: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=False)
