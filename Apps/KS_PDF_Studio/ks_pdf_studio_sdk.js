/**
 * KS PDF Studio JavaScript SDK
 * Official JavaScript client library for KS PDF Studio API
 *
 * @author Kalponic Studio
 * @version 2.0.0
 * @license MIT
 */

class KSAPIError extends Error {
  constructor(message, statusCode, responseData) {
    super(message);
    this.name = 'KSAPIError';
    this.statusCode = statusCode;
    this.responseData = responseData;
  }
}

class KSAuthenticationError extends KSAPIError {
  constructor(message, statusCode, responseData) {
    super(message, statusCode, responseData);
    this.name = 'KSAuthenticationError';
  }
}

class KSValidationError extends KSAPIError {
  constructor(message, statusCode, responseData) {
    super(message, statusCode, responseData);
    this.name = 'KSValidationError';
  }
}

class KSRateLimitError extends KSAPIError {
  constructor(message, statusCode, responseData) {
    super(message, statusCode, responseData);
    this.name = 'KSRateLimitError';
  }
}

class KSClient {
  /**
   * Create KS PDF Studio API client
   *
   * @param {Object} config Client configuration
   * @param {string} config.apiKey - Your API key
   * @param {string} [config.baseURL='https://api.kspdfstudio.com/v1'] - API base URL
   * @param {number} [config.timeout=30000] - Request timeout in milliseconds
   * @param {number} [config.maxRetries=3] - Maximum number of retries
   */
  constructor(config) {
    if (!config || !config.apiKey) {
      throw new Error('API key is required');
    }

    this.apiKey = config.apiKey;
    this.baseURL = config.baseURL || 'https://api.kspdfstudio.com/v1';
    this.timeout = config.timeout || 30000;
    this.maxRetries = config.maxRetries || 3;

    // Initialize API modules
    this.pdf = new PDFAPI(this);
    this.ai = new AIAPI(this);
    this.documents = new DocumentsAPI(this);
    this.licenses = new LicensesAPI(this);
    this.analytics = new AnalyticsAPI(this);
    this.files = new FilesAPI(this);
    this.batch = new BatchAPI(this);
    this.webhooks = new WebhooksAPI(this);
  }

  /**
   * Make API request with error handling and retries
   * @private
   */
  async _request(method, endpoint, data, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const requestTimeout = options.timeout || this.timeout;
    const retries = options.retries || this.maxRetries;

    const headers = {
      'X-API-Key': this.apiKey,
      'User-Agent': 'KS-PDF-Studio-JS-SDK/2.0.0'
    };

    let lastError;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        let response;

        if (data instanceof FormData) {
          response = await fetch(url, {
            method,
            headers: {
              'X-API-Key': this.apiKey,
              'User-Agent': 'KS-PDF-Studio-JS-SDK/2.0.0'
            },
            body: data,
            signal: AbortSignal.timeout(requestTimeout)
          });
        } else {
          headers['Content-Type'] = 'application/json';
          response = await fetch(url, {
            method,
            headers,
            body: data ? JSON.stringify(data) : undefined,
            signal: AbortSignal.timeout(requestTimeout)
          });
        }

        return await this._handleResponse(response);

      } catch (error) {
        lastError = error;

        if (attempt < retries) {
          // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
      }
    }

    throw new KSAPIError(`Request failed after ${retries + 1} attempts: ${lastError.message}`);
  }

  /**
   * Handle API response and raise appropriate exceptions
   * @private
   */
  async _handleResponse(response) {
    let data;

    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }
    } catch {
      data = {};
    }

    if (response.status === 401) {
      throw new KSAuthenticationError('Authentication failed', response.status, data);
    } else if (response.status === 400) {
      throw new KSValidationError('Validation error', response.status, data);
    } else if (response.status === 429) {
      throw new KSRateLimitError('Rate limit exceeded', response.status, data);
    } else if (!response.ok) {
      const errorMsg = (data && data.error) || `API error: ${response.status}`;
      throw new KSAPIError(errorMsg, response.status, data);
    }

    return data;
  }

  /**
   * Check API health status
   */
  async healthCheck() {
    return this._request('GET', '/health');
  }

  /**
   * Get API information
   */
  async getInfo() {
    return this._request('GET', '/info');
  }
}

class PDFAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * Generate PDF from content
   * @param {Object} options
   * @param {string} options.content - Document content
   * @param {string} [options.template='professional'] - PDF template
   * @param {string} [options.title] - Document title
   * @param {Object} [options.options] - Additional options
   */
  async generate(options) {
    return this.client._request('POST', '/pdf/generate', options);
  }

  /**
   * Extract text from PDF
   * @param {File|Blob} file - PDF file
   * @param {Object} [options={}]
   * @param {string} [options.method='text'] - Extraction method
   * @param {string} [options.pages='all'] - Pages to extract
   */
  async extract(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);

    if (options.method) formData.append('method', options.method);
    if (options.pages) formData.append('pages', options.pages);

    return this.client._request('POST', '/pdf/extract', formData);
  }

  /**
   * Add watermark to PDF
   * @param {File|Blob} file - PDF file
   * @param {Object} options
   * @param {string} options.watermarkText - Watermark text
   * @param {string} [options.watermarkType='text'] - Watermark type
   * @param {number} [options.opacity=0.3] - Opacity level
   * @param {string} [options.position='diagonal'] - Watermark position
   */
  async watermark(file, options) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('watermark_text', options.watermarkText);

    if (options.watermarkType) formData.append('watermark_type', options.watermarkType);
    if (options.opacity !== undefined) formData.append('opacity', options.opacity.toString());
    if (options.position) formData.append('position', options.position);

    return this.client._request('POST', '/pdf/watermark', formData);
  }

  /**
   * Merge multiple PDFs
   * @param {File[]|Blob[]} files - PDF files to merge
   * @param {string} [outputName] - Name for merged file
   */
  async merge(files, outputName) {
    const formData = new FormData();

    files.forEach((file, index) => {
      formData.append('files', file, `file${index + 1}.pdf`);
    });

    if (outputName) {
      formData.append('output_name', outputName);
    }

    return this.client._request('POST', '/pdf/merge', formData);
  }

  /**
   * Split PDF into multiple files
   * @param {File|Blob} file - PDF file
   * @param {Object} options
   * @param {string} [options.splitType='pages'] - Split type
   * @param {number} [options.pagesPerFile] - Pages per file
   * @param {string[]} [options.ranges] - Page ranges
   */
  async split(file, options) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('split_type', options.splitType || 'pages');

    if (options.splitType === 'pages' && options.pagesPerFile) {
      formData.append('pages_per_file', options.pagesPerFile.toString());
    } else if (options.splitType === 'ranges' && options.ranges) {
      formData.append('ranges', JSON.stringify(options.ranges));
    }

    return this.client._request('POST', '/pdf/split', formData);
  }
}

class AIAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * Enhance content with AI
   * @param {Object} options
   * @param {string} options.content - Content to enhance
   * @param {string} [options.enhancementType='general'] - Enhancement type
   * @param {Object} [options.options] - Additional options
   */
  async enhance(options) {
    return this.client._request('POST', '/ai/enhance', options);
  }

  /**
   * Generate content with AI
   * @param {Object} options
   * @param {string} options.prompt - Generation prompt
   * @param {string} [options.contentType='article'] - Content type
   * @param {string} [options.length='medium'] - Content length
   * @param {string} [options.style='professional'] - Writing style
   * @param {string} [options.audience='general'] - Target audience
   * @param {boolean} [options.includeExamples=true] - Include examples
   */
  async generate(options) {
    return this.client._request('POST', '/ai/generate', options);
  }

  /**
   * Summarize content with AI
   * @param {Object} options
   * @param {string} options.content - Content to summarize
   * @param {string} [options.summaryType='key_points'] - Summary type
   * @param {string} [options.length='medium'] - Summary length
   * @param {string} [options.format='paragraph'] - Output format
   */
  async summarize(options) {
    return this.client._request('POST', '/ai/summarize', options);
  }
}

class DocumentsAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * List documents
   * @param {Object} [options={}]
   * @param {number} [options.limit=50] - Maximum documents to return
   * @param {number} [options.offset=0] - Number of documents to skip
   * @param {string} [options.sortBy='created'] - Sort field
   * @param {string} [options.sortOrder='desc'] - Sort order
   */
  async list(options = {}) {
    const params = new URLSearchParams();

    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.sortBy) params.append('sort_by', options.sortBy);
    if (options.sortOrder) params.append('sort_order', options.sortOrder);

    const endpoint = `/documents${params.toString() ? '?' + params.toString() : ''}`;
    return this.client._request('GET', endpoint);
  }

  /**
   * Create a new document
   * @param {Object} options
   * @param {string} options.title - Document title
   * @param {string} options.content - Document content
   * @param {string} [options.template='professional'] - Document template
   * @param {Object} [options.metadata] - Document metadata
   */
  async create(options) {
    return this.client._request('POST', '/documents', options);
  }

  /**
   * Get document details
   * @param {string} documentId - Document ID
   */
  async get(documentId) {
    return this.client._request('GET', `/documents/${documentId}`);
  }

  /**
   * Update document
   * @param {string} documentId - Document ID
   * @param {Object} updates - Document updates
   */
  async update(documentId, updates) {
    return this.client._request('PUT', `/documents/${documentId}`, updates);
  }

  /**
   * Delete document
   * @param {string} documentId - Document ID
   */
  async delete(documentId) {
    return this.client._request('DELETE', `/documents/${documentId}`);
  }
}

class LicensesAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * Create a new license
   * @param {Object} options - License options
   */
  async create(options) {
    return this.client._request('POST', '/licenses', options);
  }

  /**
   * Validate a license key
   * @param {Object} options
   * @param {string} options.licenseKey - License key to validate
   * @param {string} [options.contentId] - Content ID
   * @param {string} [options.userId] - User ID
   */
  async validate(options) {
    return this.client._request('POST', '/licenses/validate', options);
  }

  /**
   * Get license details
   * @param {string} licenseId - License ID
   */
  async get(licenseId) {
    return this.client._request('GET', `/licenses/${licenseId}`);
  }
}

class AnalyticsAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * Get usage analytics
   * @param {Object} [options={}]
   * @param {number} [options.days=30] - Number of days to analyze
   * @param {string} [options.userId] - Filter by user ID
   * @param {string} [options.licenseId] - Filter by license ID
   * @param {string} [options.eventType] - Filter by event type
   */
  async usage(options = {}) {
    const params = new URLSearchParams();

    if (options.days) params.append('days', options.days.toString());
    if (options.userId) params.append('user_id', options.userId);
    if (options.licenseId) params.append('license_id', options.licenseId);
    if (options.eventType) params.append('event_type', options.eventType);

    const endpoint = `/analytics/usage${params.toString() ? '?' + params.toString() : ''}`;
    return this.client._request('GET', endpoint);
  }

  /**
   * Get revenue analytics
   * @param {Object} [options={}]
   * @param {number} [options.days=30] - Number of days to analyze
   * @param {string} [options.licenseType] - Filter by license type
   * @param {string} [options.groupBy='day'] - Group results by
   */
  async revenue(options = {}) {
    const params = new URLSearchParams();

    if (options.days) params.append('days', options.days.toString());
    if (options.licenseType) params.append('license_type', options.licenseType);
    if (options.groupBy) params.append('group_by', options.groupBy);

    const endpoint = `/analytics/revenue${params.toString() ? '?' + params.toString() : ''}`;
    return this.client._request('GET', endpoint);
  }
}

class FilesAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * Upload a file
   * @param {File|Blob} file - File to upload
   * @param {Object} [options={}]
   * @param {string} [options.category='document'] - File category
   */
  async upload(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);

    if (options.category) {
      formData.append('category', options.category);
    }

    return this.client._request('POST', '/files/upload', formData);
  }

  /**
   * Download a file
   * @param {string} fileId - File ID
   * @returns {Promise<Blob>} File blob
   */
  async download(fileId) {
    const url = `${this.client.baseURL}/files/download/${fileId}`;

    const response = await fetch(url, {
      headers: {
        'X-API-Key': this.client.apiKey,
        'User-Agent': 'KS-PDF-Studio-JS-SDK/2.0.0'
      }
    });

    if (response.status === 401) {
      throw new KSAuthenticationError('Authentication failed', response.status);
    } else if (!response.ok) {
      throw new KSAPIError(`Download failed: ${response.status}`, response.status);
    }

    return response.blob();
  }

  /**
   * Download file as URL (for browser use)
   * @param {string} fileId - File ID
   * @returns {Promise<string>} Object URL
   */
  async downloadAsURL(fileId) {
    const blob = await this.download(fileId);
    return URL.createObjectURL(blob);
  }
}

class BatchAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * Process multiple operations in batch
   * @param {Object} options
   * @param {Array} options.operations - Operations to process
   * @param {Object} [options.options] - Batch options
   */
  async process(options) {
    return this.client._request('POST', '/batch/process', options);
  }

  /**
   * Get batch processing status
   * @param {string} batchId - Batch ID
   */
  async status(batchId) {
    return this.client._request('GET', `/batch/status/${batchId}`);
  }
}

class WebhooksAPI {
  constructor(client) {
    this.client = client;
  }

  /**
   * List webhooks
   */
  async list() {
    return this.client._request('GET', '/webhooks');
  }

  /**
   * Create a webhook
   * @param {Object} options
   * @param {string} options.url - Webhook URL
   * @param {string[]} options.events - Events to listen for
   * @param {string} [options.secret] - Webhook secret
   */
  async create(options) {
    return this.client._request('POST', '/webhooks', options);
  }

  /**
   * Delete a webhook
   * @param {string} webhookId - Webhook ID
   */
  async delete(webhookId) {
    return this.client._request('DELETE', `/webhooks/${webhookId}`);
  }
}

// Convenience function to create client
function createClient(config) {
  return new KSClient(config);
}

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
  // Node.js/CommonJS
  module.exports = {
    KSClient,
    createClient,
    KSAPIError,
    KSAuthenticationError,
    KSValidationError,
    KSRateLimitError
  };
} else if (typeof define === 'function' && define.amd) {
  // AMD
  define([], function() {
    return {
      KSClient,
      createClient,
      KSAPIError,
      KSAuthenticationError,
      KSValidationError,
      KSRateLimitError
    };
  });
} else if (typeof window !== 'undefined') {
  // Browser global
  window.KSPDFStudio = {
    KSClient,
    createClient,
    KSAPIError,
    KSAuthenticationError,
    KSValidationError,
    KSRateLimitError
  };
}