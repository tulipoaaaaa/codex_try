// Application Data
const appData = {
  collectors: [
    {"name": "ISDA", "type": "Documentation", "status": "idle", "last_run": "2025-06-02", "documents": 45},
    {"name": "Anna's Archive", "type": "Books", "status": "idle", "last_run": "2025-06-01", "documents": 128},
    {"name": "GitHub", "type": "Code", "status": "running", "last_run": "2025-06-03", "documents": 89},
    {"name": "Quantopian", "type": "Research", "status": "idle", "last_run": "2025-05-30", "documents": 67},
    {"name": "arXiv", "type": "Papers", "status": "idle", "last_run": "2025-06-02", "documents": 234},
    {"name": "FRED", "type": "Economic Data", "status": "idle", "last_run": "2025-06-01", "documents": 156},
    {"name": "BitMEX", "type": "Market Data", "status": "idle", "last_run": "2025-05-29", "documents": 78},
    {"name": "SciDB", "type": "Academic", "status": "idle", "last_run": "2025-06-02", "documents": 345},
    {"name": "Web Collector", "type": "General", "status": "idle", "last_run": "2025-05-31", "documents": 123}
  ],
  domains: [
    {"name": "Crypto Derivatives", "allocation": 0.20, "current": 0.18, "documents": 456, "quality": 0.85},
    {"name": "DeFi", "allocation": 0.12, "current": 0.15, "documents": 289, "quality": 0.82},
    {"name": "High Frequency Trading", "allocation": 0.15, "current": 0.13, "documents": 378, "quality": 0.88},
    {"name": "Market Microstructure", "allocation": 0.15, "current": 0.16, "documents": 423, "quality": 0.79},
    {"name": "Portfolio Construction", "allocation": 0.10, "current": 0.09, "documents": 234, "quality": 0.76},
    {"name": "Regulation & Compliance", "allocation": 0.05, "current": 0.04, "documents": 145, "quality": 0.91},
    {"name": "Risk Management", "allocation": 0.15, "current": 0.17, "documents": 467, "quality": 0.83},
    {"name": "Valuation Models", "allocation": 0.08, "current": 0.08, "documents": 178, "quality": 0.77}
  ],
  corpus_stats: {
    "total_documents": 2570,
    "total_size_gb": 45.8,
    "processed_documents": 2234,
    "pending_processing": 336,
    "average_quality": 0.82,
    "last_updated": "2025-06-03T22:45:00Z"
  },
  recent_activity: [
    {"time": "22:43", "action": "GitHub collection started", "status": "running"},
    {"time": "22:30", "action": "PDF processing completed", "status": "success", "details": "45 files processed"},
    {"time": "22:15", "action": "arXiv collection completed", "status": "success", "details": "23 papers collected"},
    {"time": "21:58", "action": "ISDA collection completed", "status": "success", "details": "12 documents collected"},
    {"time": "21:42", "action": "Domain rebalancing started", "status": "running"}
  ],
  processing_queue: [
    {"file": "bitcoin_futures_analysis.pdf", "status": "processing", "progress": 65},
    {"file": "defi_risk_management.pdf", "status": "queued", "progress": 0},
    {"file": "market_microstructure_crypto.pdf", "status": "queued", "progress": 0}
  ]
};

// Chart colors
const chartColors = [
  '#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F', 
  '#DB4545', '#D2BA4C', '#964325', '#944454', '#13343B'
];

// Theme management
const themeToggle = document.getElementById('theme-toggle');
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

// Set initial theme based on user preference
if (prefersDarkScheme.matches) {
  document.documentElement.setAttribute('data-color-scheme', 'dark');
} else {
  document.documentElement.setAttribute('data-color-scheme', 'light');
}

// Toggle theme on button click
themeToggle.addEventListener('click', () => {
  const currentTheme = document.documentElement.getAttribute('data-color-scheme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-color-scheme', newTheme);
  showToast(`Theme changed to ${newTheme} mode`, 'success');
});

// Tab switching
const tabButtons = document.querySelectorAll('.tab-button');
const tabPanes = document.querySelectorAll('.tab-pane');

tabButtons.forEach(button => {
  button.addEventListener('click', () => {
    const tabName = button.getAttribute('data-tab');
    
    // Update active tab button
    tabButtons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');
    
    // Update active tab pane
    tabPanes.forEach(pane => pane.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');
  });
});

// Toast notification system
function showToast(message, type = 'info', duration = 3000) {
  const toastContainer = document.getElementById('toast-container');
  
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  toast.innerHTML = `
    <div class="toast-header">
      <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
      <button class="toast-close">&times;</button>
    </div>
    <div class="toast-message">${message}</div>
  `;
  
  // Add to container
  toastContainer.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => toast.classList.add('show'), 10);
  
  // Close button functionality
  const closeButton = toast.querySelector('.toast-close');
  closeButton.addEventListener('click', () => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  });
  
  // Auto remove after duration
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Modal system
const modalContainer = document.getElementById('modal-container');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalClose = document.getElementById('modal-close');
const modalCancel = document.getElementById('modal-cancel');
const modalConfirm = document.getElementById('modal-confirm');

function showModal(title, content, onConfirm = null) {
  // Set content
  modalTitle.textContent = title;
  modalBody.innerHTML = content;
  
  // Show modal
  modalContainer.classList.remove('hidden');
  
  // Set confirm action
  if (onConfirm) {
    modalConfirm.onclick = () => {
      onConfirm();
      hideModal();
    };
    modalConfirm.classList.remove('hidden');
  } else {
    modalConfirm.classList.add('hidden');
  }
  
  // Close handlers
  modalClose.onclick = hideModal;
  modalCancel.onclick = hideModal;
  modalContainer.onclick = (e) => {
    if (e.target === modalContainer) {
      hideModal();
    }
  };
}

function hideModal() {
  modalContainer.classList.add('hidden');
}

// Initialize charts
function initCharts() {
  // Domain Distribution Chart (Dashboard)
  const domainDistributionCtx = document.getElementById('domainDistributionChart').getContext('2d');
  const domainLabels = appData.domains.map(domain => domain.name);
  const domainValues = appData.domains.map(domain => domain.current * 100);
  
  new Chart(domainDistributionCtx, {
    type: 'doughnut',
    data: {
      labels: domainLabels,
      datasets: [{
        data: domainValues,
        backgroundColor: chartColors,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            font: {
              size: 10
            }
          }
        }
      }
    }
  });

  // Balancer Chart
  if (document.getElementById('balancerChart')) {
    const balancerCtx = document.getElementById('balancerChart').getContext('2d');
    const balancerData = {
      labels: domainLabels,
      datasets: [
        {
          label: 'Target Allocation',
          data: appData.domains.map(domain => domain.allocation * 100),
          backgroundColor: chartColors.map(color => color + '80'), // Add transparency
          borderColor: chartColors,
          borderWidth: 1
        },
        {
          label: 'Current Allocation',
          data: domainValues,
          backgroundColor: chartColors,
          borderColor: chartColors.map(color => color + 'FF'),
          borderWidth: 1
        }
      ]
    };
    
    new Chart(balancerCtx, {
      type: 'bar',
      data: balancerData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Allocation %'
            }
          }
        },
        plugins: {
          legend: {
            position: 'top'
          }
        }
      }
    });
  }

  // Content Type Chart (Analytics tab)
  if (document.getElementById('contentTypeChart')) {
    const contentTypeCtx = document.getElementById('contentTypeChart').getContext('2d');
    const contentTypeData = {
      labels: ['PDF', 'Code', 'Text', 'Data', 'Images', 'Other'],
      datasets: [{
        data: [45, 20, 15, 10, 5, 5],
        backgroundColor: chartColors.slice(0, 6)
      }]
    };
    
    new Chart(contentTypeCtx, {
      type: 'pie',
      data: contentTypeData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right'
          }
        }
      }
    });
  }

  // Collection Trends Chart (Analytics tab)
  if (document.getElementById('collectionTrendsChart')) {
    const trendsCtx = document.getElementById('collectionTrendsChart').getContext('2d');
    const trendsData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        {
          label: 'ISDA',
          data: [10, 15, 8, 12, 20, 45],
          borderColor: chartColors[0],
          fill: false
        },
        {
          label: 'GitHub',
          data: [30, 40, 35, 50, 60, 89],
          borderColor: chartColors[1],
          fill: false
        },
        {
          label: 'arXiv',
          data: [100, 120, 150, 180, 200, 234],
          borderColor: chartColors[2],
          fill: false
        }
      ]
    };
    
    new Chart(trendsCtx, {
      type: 'line',
      data: trendsData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Documents Collected'
            }
          }
        }
      }
    });
  }

  // Quality Analysis Chart (Analytics tab)
  if (document.getElementById('qualityAnalysisChart')) {
    const qualityCtx = document.getElementById('qualityAnalysisChart').getContext('2d');
    const qualityData = {
      labels: domainLabels,
      datasets: [{
        label: 'Quality Score',
        data: appData.domains.map(domain => domain.quality * 100),
        backgroundColor: chartColors.map(color => color + '80'),
        borderColor: chartColors,
        borderWidth: 1
      }]
    };
    
    new Chart(qualityCtx, {
      type: 'bar',
      data: qualityData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'Quality Score %'
            }
          }
        }
      }
    });
  }

  // Keyword Frequency Chart (Analytics tab)
  if (document.getElementById('keywordFrequencyChart')) {
    const keywordCtx = document.getElementById('keywordFrequencyChart').getContext('2d');
    const keywordData = {
      labels: ['Bitcoin', 'DeFi', 'Ethereum', 'Derivatives', 'Trading', 'Risk', 'Volatility', 'Liquidity', 'Options', 'Futures'],
      datasets: [{
        label: 'Frequency',
        data: [342, 289, 276, 245, 234, 198, 176, 145, 135, 124],
        backgroundColor: chartColors[0]
      }]
    };
    
    new Chart(keywordCtx, {
      type: 'bar',
      data: keywordData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Frequency'
            }
          }
        },
        indexAxis: 'y'
      }
    });
  }
}

// Initialize the collectors tab
function initCollectorsTab() {
  const collectorsGrid = document.querySelector('.collectors-grid');
  
  appData.collectors.forEach(collector => {
    const collectorCard = document.createElement('div');
    collectorCard.className = 'card collector-card';
    
    const statusClass = collector.status === 'running' ? 'status--success' : 'status--info';
    const statusText = collector.status.charAt(0).toUpperCase() + collector.status.slice(1);
    
    collectorCard.innerHTML = `
      <div class="card__header">
        <h3>${collector.name}</h3>
        <span class="status ${statusClass}">${statusText}</span>
      </div>
      <div class="card__body">
        <div class="collector-header">
          <div class="collector-type">${collector.type}</div>
          <div class="collector-last-run">Last Run: ${collector.last_run}</div>
        </div>
        
        <div class="collector-stats">
          <div class="collector-stat">
            <div class="collector-stat-value">${collector.documents}</div>
            <div class="collector-stat-label">Documents</div>
          </div>
        </div>
        
        <div class="collector-config">
          <div class="form-group">
            <label class="form-label">Search Terms</label>
            <input type="text" class="form-control" placeholder="Enter search terms...">
          </div>
          <div class="form-group">
            <label class="form-label">Max Results</label>
            <input type="number" class="form-control" value="100">
          </div>
          <div class="form-group">
            <label class="form-label">Date Range</label>
            <select class="form-control">
              <option>Last 7 days</option>
              <option selected>Last 30 days</option>
              <option>Last 90 days</option>
              <option>Last year</option>
              <option>All time</option>
            </select>
          </div>
        </div>
        
        <div class="collector-controls">
          <button class="btn btn--primary collector-start" data-collector="${collector.name}" ${collector.status === 'running' ? 'disabled' : ''}>Start Collection</button>
          <button class="btn btn--secondary collector-stop" data-collector="${collector.name}" ${collector.status !== 'running' ? 'disabled' : ''}>Stop</button>
        </div>
        
        ${collector.status === 'running' ? `
          <div class="collector-progress">
            <div class="progress-container">
              <div class="progress-bar" style="width: 45%"></div>
            </div>
            <div class="collector-progress-text">45% complete - Collecting data...</div>
          </div>
        ` : ''}
      </div>
    `;
    
    collectorsGrid.appendChild(collectorCard);
  });
  
  // Add event listeners for collector buttons
  document.querySelectorAll('.collector-start').forEach(button => {
    button.addEventListener('click', () => {
      const collectorName = button.getAttribute('data-collector');
      button.disabled = true;
      
      const stopButton = button.parentElement.querySelector('.collector-stop');
      stopButton.disabled = false;
      
      // Add progress bar
      const collectorCard = button.closest('.collector-card');
      if (!collectorCard.querySelector('.collector-progress')) {
        const progressDiv = document.createElement('div');
        progressDiv.className = 'collector-progress';
        progressDiv.innerHTML = `
          <div class="progress-container">
            <div class="progress-bar" style="width: 0%"></div>
          </div>
          <div class="collector-progress-text">0% complete - Starting collection...</div>
        `;
        collectorCard.querySelector('.card__body').appendChild(progressDiv);
        
        // Animate progress
        setTimeout(() => {
          const progressBar = progressDiv.querySelector('.progress-bar');
          progressBar.style.width = '5%';
          progressDiv.querySelector('.collector-progress-text').textContent = '5% complete - Connecting to source...';
        }, 500);
      }
      
      showToast(`Started ${collectorName} collection`, 'success');
      
      // Update status indicator
      collectorCard.querySelector('.status').className = 'status status--success';
      collectorCard.querySelector('.status').textContent = 'Running';
    });
  });
  
  document.querySelectorAll('.collector-stop').forEach(button => {
    button.addEventListener('click', () => {
      const collectorName = button.getAttribute('data-collector');
      button.disabled = true;
      
      const startButton = button.parentElement.querySelector('.collector-start');
      startButton.disabled = false;
      
      showToast(`Stopped ${collectorName} collection`, 'warning');
      
      // Update status indicator
      const collectorCard = button.closest('.collector-card');
      collectorCard.querySelector('.status').className = 'status status--info';
      collectorCard.querySelector('.status').textContent = 'Idle';
      
      // Remove progress if exists
      const progressElement = collectorCard.querySelector('.collector-progress');
      if (progressElement) {
        progressElement.remove();
      }
    });
  });
}

// Initialize processing queue
function initProcessingQueue() {
  const pdfQueue = document.getElementById('pdf-queue');
  const nonpdfQueue = document.getElementById('nonpdf-queue');
  
  if (pdfQueue) {
    pdfQueue.innerHTML = '';
    
    appData.processing_queue.forEach(item => {
      const queueItem = document.createElement('div');
      queueItem.className = 'queue-item';
      
      queueItem.innerHTML = `
        <div class="queue-item-info">
          <div class="queue-item-name">${item.file}</div>
          <div class="queue-item-progress">${item.status} - ${item.progress}%</div>
        </div>
        <div class="progress-container" style="width: 100px;">
          <div class="progress-bar" style="width: ${item.progress}%"></div>
        </div>
      `;
      
      pdfQueue.appendChild(queueItem);
    });
  }
  
  if (nonpdfQueue) {
    nonpdfQueue.innerHTML = `
      <div class="queue-item">
        <div class="queue-item-info">
          <div class="queue-item-name">trading_algorithm.py</div>
          <div class="queue-item-progress">queued - 0%</div>
        </div>
        <div class="progress-container" style="width: 100px;">
          <div class="progress-bar" style="width: 0%"></div>
        </div>
      </div>
      <div class="queue-item">
        <div class="queue-item-info">
          <div class="queue-item-name">market_data.csv</div>
          <div class="queue-item-progress">queued - 0%</div>
        </div>
        <div class="progress-container" style="width: 100px;">
          <div class="progress-bar" style="width: 0%"></div>
        </div>
      </div>
    `;
  }
  
  // Add processor start button handlers
  const startPdfProcessor = document.getElementById('start-pdf-processor');
  const stopPdfProcessor = document.getElementById('stop-pdf-processor');
  const startNonpdfProcessor = document.getElementById('start-nonpdf-processor');
  const stopNonpdfProcessor = document.getElementById('stop-nonpdf-processor');
  
  if (startPdfProcessor) {
    startPdfProcessor.addEventListener('click', () => {
      startPdfProcessor.disabled = true;
      stopPdfProcessor.disabled = false;
      showToast('PDF processing started', 'success');
      
      // Start processing animation
      const queueItems = pdfQueue.querySelectorAll('.queue-item');
      if (queueItems.length > 0) {
        const firstItem = queueItems[0];
        const progressBar = firstItem.querySelector('.progress-bar');
        const progressText = firstItem.querySelector('.queue-item-progress');
        
        progressText.textContent = 'processing - 5%';
        progressBar.style.width = '5%';
        
        // Simulate progress
        let progress = 5;
        const progressInterval = setInterval(() => {
          progress += 5;
          if (progress <= 100) {
            progressBar.style.width = progress + '%';
            progressText.textContent = `processing - ${progress}%`;
          } else {
            clearInterval(progressInterval);
            progressText.textContent = 'completed - 100%';
            showToast('PDF processing completed for ' + firstItem.querySelector('.queue-item-name').textContent, 'success');
          }
        }, 1000);
      }
    });
  }
  
  if (stopPdfProcessor) {
    stopPdfProcessor.addEventListener('click', () => {
      startPdfProcessor.disabled = false;
      stopPdfProcessor.disabled = true;
      showToast('PDF processing stopped', 'warning');
    });
  }
  
  if (startNonpdfProcessor) {
    startNonpdfProcessor.addEventListener('click', () => {
      startNonpdfProcessor.disabled = true;
      stopNonpdfProcessor.disabled = false;
      showToast('Non-PDF processing started', 'success');
      
      // Start processing animation
      const queueItems = nonpdfQueue.querySelectorAll('.queue-item');
      if (queueItems.length > 0) {
        const firstItem = queueItems[0];
        const progressBar = firstItem.querySelector('.progress-bar');
        const progressText = firstItem.querySelector('.queue-item-progress');
        
        progressText.textContent = 'processing - 5%';
        progressBar.style.width = '5%';
        
        // Simulate progress
        let progress = 5;
        const progressInterval = setInterval(() => {
          progress += 10;
          if (progress <= 100) {
            progressBar.style.width = progress + '%';
            progressText.textContent = `processing - ${progress}%`;
          } else {
            clearInterval(progressInterval);
            progressText.textContent = 'completed - 100%';
            showToast('Non-PDF processing completed for ' + firstItem.querySelector('.queue-item-name').textContent, 'success');
          }
        }, 800);
      }
    });
  }
  
  if (stopNonpdfProcessor) {
    stopNonpdfProcessor.addEventListener('click', () => {
      startNonpdfProcessor.disabled = false;
      stopNonpdfProcessor.disabled = true;
      showToast('Non-PDF processing stopped', 'warning');
    });
  }
  
  // Batch operation buttons
  const batchButtons = document.querySelectorAll('.batch-operations button');
  batchButtons.forEach(button => {
    button.addEventListener('click', () => {
      const operation = button.textContent;
      showToast(`${operation} operation started`, 'info');
      
      // Simulate completion after a delay
      setTimeout(() => {
        showToast(`${operation} operation completed successfully`, 'success');
      }, 3000);
    });
  });
}

// Initialize corpus manager
function initCorpusManager() {
  const domainTree = document.getElementById('domain-tree');
  const corpusResults = document.getElementById('corpus-results');
  
  if (domainTree) {
    domainTree.innerHTML = '';
    
    // Add all domains item
    const allDomainsItem = document.createElement('div');
    allDomainsItem.className = 'domain-tree-item active';
    allDomainsItem.textContent = 'All Domains';
    domainTree.appendChild(allDomainsItem);
    
    // Add domain items
    appData.domains.forEach(domain => {
      const domainItem = document.createElement('div');
      domainItem.className = 'domain-tree-item';
      domainItem.textContent = domain.name;
      domainTree.appendChild(domainItem);
    });
    
    // Make domain items clickable
    domainTree.querySelectorAll('.domain-tree-item').forEach(item => {
      item.addEventListener('click', () => {
        domainTree.querySelectorAll('.domain-tree-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        showToast(`Switched to ${item.textContent} domain`, 'info');
      });
    });
  }
  
  if (corpusResults) {
    corpusResults.innerHTML = '';
    
    // Add sample results
    const sampleFiles = [
      {
        title: 'Bitcoin Futures Market Analysis',
        domain: 'Crypto Derivatives',
        type: 'PDF',
        date: '2025-05-28',
        size: '2.4 MB',
        quality: 0.87,
        snippet: 'This comprehensive analysis explores the dynamics of Bitcoin futures markets, including liquidity profiles, basis trading strategies, and market microstructure effects.'
      },
      {
        title: 'DeFi Lending Protocol Risk Assessment',
        domain: 'DeFi',
        type: 'PDF',
        date: '2025-06-01',
        size: '1.8 MB',
        quality: 0.92,
        snippet: 'An examination of risk factors in decentralized lending protocols, covering smart contract vulnerabilities, governance risks, and economic attack vectors.'
      },
      {
        title: 'High Frequency Trading on Decentralized Exchanges',
        domain: 'High Frequency Trading',
        type: 'Research',
        date: '2025-05-25',
        size: '3.1 MB',
        quality: 0.84,
        snippet: 'This paper examines latency arbitrage opportunities in DEX environments, MEV strategies, and optimal order routing for high-frequency crypto trading operations.'
      },
      {
        title: 'Crypto Market Volatility Modeling',
        domain: 'Market Microstructure',
        type: 'Code',
        date: '2025-06-02',
        size: '1.2 MB',
        quality: 0.89,
        snippet: 'Implementation of advanced volatility models (GARCH, EGARCH, SV) specifically calibrated for cryptocurrency markets with extreme tail events.'
      },
      {
        title: 'Regulatory Frameworks for Digital Assets',
        domain: 'Regulation & Compliance',
        type: 'PDF',
        date: '2025-05-30',
        size: '4.5 MB',
        quality: 0.95,
        snippet: 'A comprehensive review of global regulatory approaches to digital assets, focusing on securities classification, custody requirements, and compliance protocols.'
      }
    ];
    
    sampleFiles.forEach(file => {
      const resultItem = document.createElement('div');
      resultItem.className = 'corpus-result-item';
      
      resultItem.innerHTML = `
        <div class="corpus-result-header">
          <div>
            <div class="corpus-result-title">${file.title}</div>
            <div class="corpus-result-meta">
              <span>${file.domain}</span>
              <span>${file.type}</span>
              <span>${file.date}</span>
              <span>${file.size}</span>
              <span>Quality: ${Math.round(file.quality * 100)}%</span>
            </div>
          </div>
          <div>
            <button class="btn btn--sm btn--secondary">View</button>
          </div>
        </div>
        <div class="corpus-result-snippet">
          ${file.snippet}
        </div>
      `;
      
      corpusResults.appendChild(resultItem);
      
      // Add click event to view buttons
      const viewButton = resultItem.querySelector('button');
      viewButton.addEventListener('click', () => {
        showModal(file.title, `
          <div class="file-details">
            <p><strong>Domain:</strong> ${file.domain}</p>
            <p><strong>Type:</strong> ${file.type}</p>
            <p><strong>Date:</strong> ${file.date}</p>
            <p><strong>Size:</strong> ${file.size}</p>
            <p><strong>Quality Score:</strong> ${Math.round(file.quality * 100)}%</p>
            <p><strong>Path:</strong> G:/corpus/${file.domain.toLowerCase().replace(/ /g, '_')}/${file.title.toLowerCase().replace(/ /g, '_')}.pdf</p>
            <hr>
            <h4>Abstract/Summary</h4>
            <p>${file.snippet}</p>
            <p>This would display the full metadata and content preview for the selected document. In the desktop application, you would be able to open the file directly or edit its metadata from this interface.</p>
          </div>
        `);
      });
    });
  }
}

// Initialize balancer tab
function initBalancerTab() {
  const allocationTableBody = document.getElementById('allocation-table-body');
  
  if (allocationTableBody) {
    allocationTableBody.innerHTML = '';
    
    appData.domains.forEach(domain => {
      const row = document.createElement('tr');
      
      const allocPercentTarget = (domain.allocation * 100).toFixed(1);
      const allocPercentCurrent = (domain.current * 100).toFixed(1);
      const qualityPercent = (domain.quality * 100).toFixed(0);
      
      // Determine if we need more or less content
      let actionText = 'Balanced';
      let actionClass = 'status--success';
      
      if (domain.current < domain.allocation - 0.01) {
        actionText = 'Need More';
        actionClass = 'status--warning';
      } else if (domain.current > domain.allocation + 0.01) {
        actionText = 'Overrepresented';
        actionClass = 'status--error';
      }
      
      row.innerHTML = `
        <td>${domain.name}</td>
        <td>
          <input type="range" class="allocation-slider" min="0" max="30" value="${allocPercentTarget}" 
            data-domain="${domain.name}">
          <span class="allocation-value">${allocPercentTarget}%</span>
        </td>
        <td>${allocPercentCurrent}%</td>
        <td>${domain.documents}</td>
        <td>${qualityPercent}%</td>
        <td><span class="status ${actionClass}">${actionText}</span></td>
      `;
      
      allocationTableBody.appendChild(row);
    });
    
    // Add event listeners to sliders
    const sliders = allocationTableBody.querySelectorAll('.allocation-slider');
    sliders.forEach(slider => {
      slider.addEventListener('input', function() {
        const valueDisplay = this.nextElementSibling;
        valueDisplay.textContent = this.value + '%';
      });
    });
    
    // Add rebalance button handler
    const rebalanceButton = document.getElementById('rebalance-corpus');
    if (rebalanceButton) {
      rebalanceButton.addEventListener('click', () => {
        showModal('Confirm Rebalancing', `
          <p>This will analyze your current corpus and suggest operations to bring it in line with target allocations:</p>
          <ul>
            <li>Move 12 documents from DeFi to Crypto Derivatives</li>
            <li>Collect 25 more documents for High Frequency Trading</li>
            <li>Reduce Risk Management by 18 documents</li>
          </ul>
          <p>Do you want to proceed with automatic rebalancing?</p>
        `, () => {
          showToast('Corpus rebalancing started', 'success');
          
          // Simulate completion
          setTimeout(() => {
            showToast('Corpus rebalancing completed successfully', 'success');
            
            // Update some allocation values to show change
            const defiRow = allocationTableBody.querySelectorAll('tr')[1];
            const hftRow = allocationTableBody.querySelectorAll('tr')[2];
            const riskRow = allocationTableBody.querySelectorAll('tr')[6];
            
            if (defiRow) defiRow.querySelectorAll('td')[2].textContent = '12.5%';
            if (hftRow) hftRow.querySelectorAll('td')[2].textContent = '14.2%';
            if (riskRow) riskRow.querySelectorAll('td')[2].textContent = '15.8%';
            
            // Update status indicators
            const statuses = allocationTableBody.querySelectorAll('.status');
            statuses.forEach(status => {
              status.className = 'status status--success';
              status.textContent = 'Balanced';
            });
          }, 5000);
        });
      });
    }
    
    // Save allocations button
    const saveAllocationsButton = document.getElementById('save-allocations');
    if (saveAllocationsButton) {
      saveAllocationsButton.addEventListener('click', () => {
        const newAllocations = [];
        
        sliders.forEach(slider => {
          newAllocations.push({
            domain: slider.getAttribute('data-domain'),
            allocation: parseFloat(slider.value) / 100
          });
        });
        
        showToast('Domain allocations saved successfully', 'success');
      });
    }
  }
}

// Initialize domain configuration
function initDomainConfig() {
  const domainConfigList = document.querySelector('.domain-config-list');
  
  if (domainConfigList) {
    domainConfigList.innerHTML = '';
    
    appData.domains.forEach(domain => {
      const domainItem = document.createElement('div');
      domainItem.className = 'api-key-item';
      
      domainItem.innerHTML = `
        <div class="api-key-name">${domain.name}</div>
        <div class="api-key-value">Target: ${(domain.allocation * 100).toFixed(1)}%</div>
        <button class="btn btn--sm btn--secondary">Edit</button>
      `;
      
      domainConfigList.appendChild(domainItem);
      
      // Add edit button handler
      const editButton = domainItem.querySelector('button');
      editButton.addEventListener('click', () => {
        showModal('Edit Domain Configuration', `
          <div class="form-group">
            <label class="form-label">Domain Name</label>
            <input type="text" class="form-control" value="${domain.name}">
          </div>
          <div class="form-group">
            <label class="form-label">Target Allocation (%)</label>
            <input type="number" class="form-control" value="${(domain.allocation * 100).toFixed(1)}" min="0" max="100" step="0.1">
          </div>
          <div class="form-group">
            <label class="form-label">Minimum Quality Threshold (%)</label>
            <input type="number" class="form-control" value="75" min="0" max="100">
          </div>
          <div class="form-group">
            <label class="form-label">Keywords (comma separated)</label>
            <input type="text" class="form-control" value="bitcoin, crypto, trading, derivatives">
          </div>
        `, () => {
          showToast(`Domain configuration for ${domain.name} updated`, 'success');
        });
      });
    });
  }
}

// Initialize logs tab
function initLogsTab() {
  const logsViewer = document.getElementById('logs-viewer');
  
  if (logsViewer) {
    logsViewer.innerHTML = '';
    
    // Generate sample logs
    const logTypes = ['info', 'warning', 'error', 'debug'];
    const logSources = ['Collector', 'Processor', 'System', 'Balancer', 'Storage'];
    const logMessages = [
      'Started collection process',
      'API request completed successfully',
      'Document processed and indexed',
      'Connection established to external service',
      'Failed to parse document metadata',
      'Rate limit exceeded, retrying in 60 seconds',
      'Invalid file format detected',
      'Cache hit for document ID #1234',
      'Rebalancing operation completed',
      'System configuration loaded from file',
      'Memory usage warning threshold exceeded',
      'Document quality below threshold, marked for review',
      'Network connectivity issue detected',
      'Successfully authenticated with external API',
      'Corpus update operation completed'
    ];
    
    // Current time for logs
    const now = new Date();
    
    // Generate 50 log entries
    for (let i = 0; i < 50; i++) {
      const logEntry = document.createElement('div');
      logEntry.className = 'log-entry';
      
      const logTime = new Date(now - i * 30000); // 30 seconds between logs
      const timeString = logTime.toTimeString().split(' ')[0];
      
      const logType = logTypes[Math.floor(Math.random() * logTypes.length)];
      const logSource = logSources[Math.floor(Math.random() * logSources.length)];
      const logMessage = logMessages[Math.floor(Math.random() * logMessages.length)];
      
      logEntry.innerHTML = `
        <div class="log-timestamp">${timeString}</div>
        <div class="log-level ${logType}">${logType.toUpperCase()}</div>
        <div class="log-message">[${logSource}] ${logMessage}</div>
      `;
      
      logsViewer.appendChild(logEntry);
    }
    
    // Add filter functionality
    const logFilterInput = document.querySelector('.logs-controls input');
    if (logFilterInput) {
      logFilterInput.addEventListener('input', function() {
        const filterText = this.value.toLowerCase();
        
        document.querySelectorAll('.log-entry').forEach(entry => {
          const message = entry.querySelector('.log-message').textContent.toLowerCase();
          if (message.includes(filterText)) {
            entry.style.display = '';
          } else {
            entry.style.display = 'none';
          }
        });
      });
    }
    
    // Add log level filtering
    const logLevelCheckboxes = document.querySelectorAll('.log-level-filters input');
    logLevelCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('change', function() {
        const logLevel = this.parentElement.textContent.trim().toLowerCase();
        const isChecked = this.checked;
        
        document.querySelectorAll(`.log-level.${logLevel}`).forEach(level => {
          const logEntry = level.closest('.log-entry');
          if (isChecked) {
            logEntry.style.display = '';
          } else {
            logEntry.style.display = 'none';
          }
        });
      });
    });
  }
}

// Initialize Activity List
function initActivityList() {
  const activityList = document.getElementById('activity-list');
  
  if (activityList) {
    activityList.innerHTML = '';
    
    appData.recent_activity.forEach(activity => {
      const activityItem = document.createElement('div');
      activityItem.className = 'activity-item';
      
      activityItem.innerHTML = `
        <div class="activity-time">${activity.time}</div>
        <div>
          <div class="activity-action">${activity.action}</div>
          ${activity.details ? `<div class="activity-details">${activity.details}</div>` : ''}
        </div>
        <div>
          <span class="status status--${activity.status === 'running' ? 'success' : 'info'}">${activity.status}</span>
        </div>
      `;
      
      activityList.appendChild(activityItem);
    });
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Initialize charts
  initCharts();
  
  // Initialize collectors tab
  initCollectorsTab();
  
  // Initialize processing queue
  initProcessingQueue();
  
  // Initialize corpus manager
  initCorpusManager();
  
  // Initialize balancer tab
  initBalancerTab();
  
  // Initialize domain configuration
  initDomainConfig();
  
  // Initialize logs tab
  initLogsTab();
  
  // Initialize activity list
  initActivityList();
  
  // Show welcome toast
  setTimeout(() => {
    showToast('Welcome to CryptoFinance Corpus Builder', 'success', 5000);
  }, 1000);
});