#!/usr/bin/env node

/**
 * Maestro Schema Validation Utilities
 *
 * Validates JSON files against Maestro schemas using JSON Schema.
 * Supports both Node.js CLI usage and programmatic API.
 *
 * Usage:
 *   node validate.js <schema-name> <json-file>
 *   node validate.js session-metadata ./sessions/xyz/metadata.json
 *
 * @module maestro-schema-validator
 */

const fs = require('fs');
const path = require('path');

/**
 * Validate JSON data against a schema
 *
 * @param {object} data - The JSON data to validate
 * @param {object} schema - The JSON Schema to validate against
 * @param {string} schemaName - Name of the schema for error messages
 * @returns {object} Validation result with {valid: boolean, errors: array}
 */
function validate(data, schema, schemaName = 'schema') {
  const errors = [];

  // Basic schema validation
  if (!schema || typeof schema !== 'object') {
    return {
      valid: false,
      errors: [`Schema ${schemaName} is invalid or missing`]
    };
  }

  // Check required properties
  if (schema.required && Array.isArray(schema.required)) {
    for (const required of schema.required) {
      if (!(required in data)) {
        errors.push({
          property: required,
          message: `Required property '${required}' is missing`,
          constraint: 'required'
        });
      }
    }
  }

  // Check property types and constraints
  if (schema.properties) {
    for (const [propName, propSchema] of Object.entries(schema.properties)) {
      if (!(propName in data)) continue;

      const value = data[propName];
      const propErrors = validateProperty(value, propSchema, propName);
      errors.push(...propErrors);
    }
  }

  // Check array items if applicable
  if (schema.items && Array.isArray(data)) {
    data.forEach((item, index) => {
      const itemErrors = validateProperty(item, schema.items, `[${index}]`);
      errors.push(...itemErrors);
    });
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate a single property against its schema
 *
 * @param {any} value - The property value
 * @param {object} propSchema - The property schema
 * @param {string} propName - Property name for error messages
 * @returns {array} Array of error objects
 */
function validateProperty(value, propSchema, propName) {
  const errors = [];

  // Type validation
  if (propSchema.type) {
    const typeErrors = validateType(value, propSchema.type, propName);
    errors.push(...typeErrors);
  }

  // Enum validation
  if (propSchema.enum && !propSchema.enum.includes(value)) {
    errors.push({
      property: propName,
      message: `Value '${value}' is not one of: ${propSchema.enum.join(', ')}`,
      constraint: 'enum',
      value
    });
  }

  // Format validation
  if (propSchema.format) {
    const formatErrors = validateFormat(value, propSchema.format, propName);
    errors.push(...formatErrors);
  }

  // Pattern validation
  if (propSchema.pattern) {
    const regex = new RegExp(propSchema.pattern);
    if (!regex.test(value)) {
      errors.push({
        property: propName,
        message: `Value '${value}' does not match pattern: ${propSchema.pattern}`,
        constraint: 'pattern',
        value
      });
    }
  }

  // Range validation
  if (typeof value === 'number') {
    if (propSchema.minimum !== undefined && value < propSchema.minimum) {
      errors.push({
        property: propName,
        message: `Value ${value} is less than minimum ${propSchema.minimum}`,
        constraint: 'minimum',
        value
      });
    }
    if (propSchema.maximum !== undefined && value > propSchema.maximum) {
      errors.push({
        property: propName,
        message: `Value ${value} is greater than maximum ${propSchema.maximum}`,
        constraint: 'maximum',
        value
      });
    }
  }

  // Array length validation
  if (Array.isArray(value)) {
    if (propSchema.minItems !== undefined && value.length < propSchema.minItems) {
      errors.push({
        property: propName,
        message: `Array length ${value.length} is less than minimum ${propSchema.minItems}`,
        constraint: 'minItems',
        value
      });
    }
    if (propSchema.maxItems !== undefined && value.length > propSchema.maxItems) {
      errors.push({
        property: propName,
        message: `Array length ${value.length} is greater than maximum ${propSchema.maxItems}`,
        constraint: 'maxItems',
        value
      });
    }
  }

  // Nested object validation
  if (propSchema.properties && typeof value === 'object' && value !== null && !Array.isArray(value)) {
    const nestedErrors = validate(value, propSchema, propName).errors;
    errors.push(...nestedErrors);
  }

  // Array items validation
  if (propSchema.items && Array.isArray(value)) {
    value.forEach((item, index) => {
      const itemErrors = validateProperty(item, propSchema.items, `${propName}[${index}]`);
      errors.push(...itemErrors);
    });
  }

  return errors;
}

/**
 * Validate value type
 *
 * @param {any} value - The value to validate
 * @param {string|Array} type - Expected type(s)
 * @param {string} propName - Property name for error messages
 * @returns {array} Array of error objects
 */
function validateType(value, type, propName) {
  const errors = [];
  const types = Array.isArray(type) ? type : [type];

  const isValid = types.some(expectedType => {
    switch (expectedType) {
      case 'string':
        return typeof value === 'string';
      case 'number':
        return typeof value === 'number' && !isNaN(value);
      case 'integer':
        return Number.isInteger(value);
      case 'boolean':
        return typeof value === 'boolean';
      case 'object':
        return typeof value === 'object' && value !== null && !Array.isArray(value);
      case 'array':
        return Array.isArray(value);
      case 'null':
        return value === null;
      default:
        return true;
    }
  });

  if (!isValid) {
    const actualType = Array.isArray(value) ? 'array' : value === null ? 'null' : typeof value;
    errors.push({
      property: propName,
      message: `Expected type ${types.join(' or ')}, got ${actualType}`,
      constraint: 'type',
      value
    });
  }

  return errors;
}

/**
 * Validate value format
 *
 * @param {string} value - The value to validate
 * @param {string} format - Expected format
 * @param {string} propName - Property name for error messages
 * @returns {array} Array of error objects
 */
function validateFormat(value, format, propName) {
  const errors = [];

  const formats = {
    'date-time': /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$/,
    'uuid': /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    'email': /^[^\s@]+@[^\s@]+\.[^\s@]+$$/,
    'uri': /^https?:\/\/.+/
  };

  const pattern = formats[format];
  if (pattern && !pattern.test(value)) {
    errors.push({
      property: propName,
      message: `Value '${value}' does not match format: ${format}`,
      constraint: 'format',
      value
    });
  }

  return errors;
}

/**
 * Load and parse a JSON file
 *
 * @param {string} filePath - Path to JSON file
 * @returns {object} Parsed JSON data
 * @throws {Error} If file cannot be read or parsed
 */
function loadJsonFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    throw new Error(`Failed to load JSON file '${filePath}': ${error.message}`);
  }
}

/**
 * Load a schema by name
 *
 * @param {string} schemaName - Name of the schema (without .schema.json)
 * @param {string} schemasDir - Directory containing schemas
 * @returns {object} Schema object
 */
function loadSchema(schemaName, schemasDir = __dirname) {
  const schemaPath = path.join(schemasDir, `${schemaName}.schema.json`);

  if (!fs.existsSync(schemaPath)) {
    throw new Error(`Schema not found: ${schemaName}`);
  }

  return loadJsonFile(schemaPath);
}

/**
 * Format validation errors for display
 *
 * @param {Array} errors - Array of error objects
 * @returns {string} Formatted error messages
 */
function formatErrors(errors) {
  if (errors.length === 0) return '';

  return errors.map(error => {
    let msg = `  - ${error.property}`;
    if (error.message) {
      msg += `: ${error.message}`;
    }
    if (error.constraint) {
      msg += ` [${error.constraint}]`;
    }
    return msg;
  }).join('\n');
}

/**
 * CLI entry point
 */
function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node validate.js <schema-name> <json-file>');
    console.error('');
    console.error('Available schemas:');
    console.error('  - session-metadata');
    console.error('  - decisions');
    console.error('  - checkpoints');
    console.error('  - historical-tech-stack');
    console.error('  - historical-architecture');
    console.error('  - historical-task-ordering');
    console.error('  - config');
    process.exit(1);
  }

  const [schemaName, jsonFilePath] = args;

  try {
    const schema = loadSchema(schemaName);
    const data = loadJsonFile(jsonFilePath);

    const result = validate(data, schema, schemaName);

    if (result.valid) {
      console.log(`✓ Validation passed: ${jsonFilePath}`);
      process.exit(0);
    } else {
      console.error(`✗ Validation failed: ${jsonFilePath}`);
      console.error('');
      console.error('Errors:');
      console.error(formatErrors(result.errors));
      process.exit(1);
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Export for programmatic use
module.exports = {
  validate,
  validateProperty,
  validateType,
  validateFormat,
  loadJsonFile,
  loadSchema,
  formatErrors
};

// Run CLI if executed directly
if (require.main === module) {
  main();
}
