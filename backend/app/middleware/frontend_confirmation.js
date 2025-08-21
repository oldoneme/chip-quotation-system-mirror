/**
 * 前端确认对话框组件
 * 用于敏感操作的二次确认
 */

class ConfirmationDialog {
    constructor() {
        this.isOpen = false;
        this.currentConfirmation = null;
        this.dialogElement = null;
        this.createDialog();
    }

    createDialog() {
        // 创建对话框HTML结构
        const dialogHTML = `
            <div id="confirmation-dialog" class="confirmation-overlay" style="display: none;">
                <div class="confirmation-modal">
                    <div class="confirmation-header">
                        <h3 id="confirmation-title">操作确认</h3>
                        <span class="confirmation-risk-level" id="confirmation-risk-level"></span>
                    </div>
                    
                    <div class="confirmation-content">
                        <div class="confirmation-warning">
                            <span class="warning-icon">⚠️</span>
                            <p id="confirmation-description">此操作需要您的确认</p>
                        </div>
                        
                        <div class="confirmation-details" id="confirmation-details">
                            <!-- 操作详情将在这里显示 -->
                        </div>
                        
                        <div class="confirmation-form">
                            <div class="form-group">
                                <label for="password-confirmation">请输入密码确认:</label>
                                <input type="password" id="password-confirmation" 
                                       placeholder="输入您的密码" required>
                            </div>
                            
                            <div class="form-group" id="reason-group" style="display: none;">
                                <label for="operation-reason">操作原因:</label>
                                <textarea id="operation-reason" 
                                         placeholder="请说明执行此操作的原因"
                                         rows="3"></textarea>
                            </div>
                            
                            <div class="form-group" id="additional-fields">
                                <!-- 额外的确认字段将在这里显示 -->
                            </div>
                        </div>
                        
                        <div class="confirmation-timeout">
                            <span id="timeout-message">此确认将在 <span id="timeout-countdown"></span> 后过期</span>
                        </div>
                        
                        <div class="admin-approval-notice" id="admin-approval-notice" style="display: none;">
                            <p>⚠️ 此操作需要管理员批准</p>
                        </div>
                    </div>
                    
                    <div class="confirmation-buttons">
                        <button id="confirm-button" class="btn btn-danger">确认执行</button>
                        <button id="cancel-button" class="btn btn-secondary">取消</button>
                    </div>
                </div>
            </div>
        `;

        // 添加样式
        const styles = `
            <style>
                .confirmation-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.7);
                    z-index: 10000;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                
                .confirmation-modal {
                    background: white;
                    border-radius: 8px;
                    padding: 0;
                    max-width: 500px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                }
                
                .confirmation-header {
                    background-color: #f8f9fa;
                    padding: 15px 20px;
                    border-bottom: 1px solid #dee2e6;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .confirmation-header h3 {
                    margin: 0;
                    color: #495057;
                }
                
                .confirmation-risk-level {
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                    text-transform: uppercase;
                }
                
                .confirmation-risk-level.medium { background-color: #ffc107; color: #212529; }
                .confirmation-risk-level.high { background-color: #fd7e14; color: white; }
                .confirmation-risk-level.critical { background-color: #dc3545; color: white; }
                
                .confirmation-content {
                    padding: 20px;
                }
                
                .confirmation-warning {
                    display: flex;
                    align-items: center;
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                
                .warning-icon {
                    font-size: 24px;
                    margin-right: 10px;
                }
                
                .confirmation-details {
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 20px;
                    font-family: monospace;
                    font-size: 14px;
                }
                
                .form-group {
                    margin-bottom: 15px;
                }
                
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #495057;
                }
                
                .form-group input,
                .form-group textarea,
                .form-group select {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    font-size: 14px;
                }
                
                .form-group input:focus,
                .form-group textarea:focus,
                .form-group select:focus {
                    outline: none;
                    border-color: #80bdff;
                    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
                }
                
                .confirmation-timeout {
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                    margin-bottom: 15px;
                }
                
                .admin-approval-notice {
                    background-color: #d1ecf1;
                    border: 1px solid #bee5eb;
                    border-radius: 4px;
                    padding: 10px;
                    margin-bottom: 15px;
                    text-align: center;
                }
                
                .confirmation-buttons {
                    padding: 15px 20px;
                    border-top: 1px solid #dee2e6;
                    display: flex;
                    justify-content: flex-end;
                    gap: 10px;
                }
                
                .btn {
                    padding: 8px 16px;
                    border: 1px solid;
                    border-radius: 4px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                
                .btn-danger {
                    background-color: #dc3545;
                    border-color: #dc3545;
                    color: white;
                }
                
                .btn-danger:hover {
                    background-color: #c82333;
                    border-color: #bd2130;
                }
                
                .btn-secondary {
                    background-color: #6c757d;
                    border-color: #6c757d;
                    color: white;
                }
                
                .btn-secondary:hover {
                    background-color: #5a6268;
                    border-color: #545b62;
                }
                
                #timeout-countdown {
                    font-weight: bold;
                    color: #dc3545;
                }
            </style>
        `;

        // 添加到页面
        document.head.insertAdjacentHTML('beforeend', styles);
        document.body.insertAdjacentHTML('beforeend', dialogHTML);

        this.dialogElement = document.getElementById('confirmation-dialog');
        
        // 绑定事件
        this.bindEvents();
    }

    bindEvents() {
        const confirmButton = document.getElementById('confirm-button');
        const cancelButton = document.getElementById('cancel-button');
        
        confirmButton.addEventListener('click', () => this.handleConfirm());
        cancelButton.addEventListener('click', () => this.handleCancel());
        
        // ESC键取消
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.handleCancel();
            }
        });
        
        // 点击遮罩层取消
        this.dialogElement.addEventListener('click', (e) => {
            if (e.target === this.dialogElement) {
                this.handleCancel();
            }
        });
    }

    show(confirmationData) {
        this.currentConfirmation = confirmationData;
        this.isOpen = true;
        
        // 更新对话框内容
        this.updateDialogContent(confirmationData);
        
        // 显示对话框
        this.dialogElement.style.display = 'flex';
        
        // 开始倒计时
        this.startCountdown(confirmationData.timeout_seconds);
        
        // 聚焦到密码输入框
        setTimeout(() => {
            document.getElementById('password-confirmation').focus();
        }, 100);
        
        return new Promise((resolve, reject) => {
            this.resolvePromise = resolve;
            this.rejectPromise = reject;
        });
    }

    hide() {
        this.isOpen = false;
        this.currentConfirmation = null;
        this.dialogElement.style.display = 'none';
        
        // 清除倒计时
        if (this.countdownTimer) {
            clearInterval(this.countdownTimer);
        }
    }

    updateDialogContent(confirmationData) {
        // 更新标题和描述
        document.getElementById('confirmation-title').textContent = confirmationData.operation_name;
        document.getElementById('confirmation-description').textContent = confirmationData.description;
        
        // 更新风险等级
        const riskLevelElement = document.getElementById('confirmation-risk-level');
        riskLevelElement.textContent = confirmationData.risk_level;
        riskLevelElement.className = `confirmation-risk-level ${confirmationData.risk_level}`;
        
        // 更新操作详情
        const detailsElement = document.getElementById('confirmation-details');
        const operationData = confirmationData.operation_data || {};
        const detailsHTML = Object.entries(operationData).map(([key, value]) => {
            return `<div><strong>${key}:</strong> ${JSON.stringify(value)}</div>`;
        }).join('');
        detailsElement.innerHTML = detailsHTML;
        
        // 显示/隐藏管理员批准通知
        const adminNotice = document.getElementById('admin-approval-notice');
        if (confirmationData.admin_approval_required) {
            adminNotice.style.display = 'block';
        } else {
            adminNotice.style.display = 'none';
        }
        
        // 清空表单
        document.getElementById('password-confirmation').value = '';
        document.getElementById('operation-reason').value = '';
    }

    startCountdown(timeoutSeconds) {
        let remainingSeconds = timeoutSeconds;
        const countdownElement = document.getElementById('timeout-countdown');
        
        const updateCountdown = () => {
            const minutes = Math.floor(remainingSeconds / 60);
            const seconds = remainingSeconds % 60;
            countdownElement.textContent = `${minutes}分${seconds.toString().padStart(2, '0')}秒`;
            
            if (remainingSeconds <= 0) {
                this.handleTimeout();
                return;
            }
            
            remainingSeconds--;
        };
        
        updateCountdown();
        this.countdownTimer = setInterval(updateCountdown, 1000);
    }

    handleConfirm() {
        const password = document.getElementById('password-confirmation').value;
        const reason = document.getElementById('operation-reason').value;
        
        if (!password) {
            alert('请输入密码确认');
            return;
        }
        
        const confirmationData = {
            password_confirmation: password,
            additional_data: {
                reason: reason
            }
        };
        
        if (this.resolvePromise) {
            this.resolvePromise(confirmationData);
        }
        
        this.hide();
    }

    handleCancel() {
        if (this.rejectPromise) {
            this.rejectPromise(new Error('用户取消操作'));
        }
        
        this.hide();
    }

    handleTimeout() {
        if (this.rejectPromise) {
            this.rejectPromise(new Error('确认已超时'));
        }
        
        this.hide();
    }
}

// 确认管理器
class ConfirmationManager {
    constructor() {
        this.dialog = new ConfirmationDialog();
        this.baseURL = '/api/v1/confirmations';
    }

    async requestConfirmation(operation, operationData) {
        try {
            const response = await fetch(`${this.baseURL}/request`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    operation: operation,
                    operation_data: operationData
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                return result;
            } else {
                throw new Error(result.detail || '确认请求失败');
            }
        } catch (error) {
            throw error;
        }
    }

    async confirmOperation(token, confirmationData) {
        try {
            const response = await fetch(`${this.baseURL}/confirm/${token}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(confirmationData)
            });

            const result = await response.json();
            
            if (response.ok) {
                return result;
            } else {
                throw new Error(result.detail || '确认失败');
            }
        } catch (error) {
            throw error;
        }
    }

    async executeWithConfirmation(operation, operationData, actualOperation) {
        try {
            // 1. 请求确认
            const confirmationInfo = await this.requestConfirmation(operation, operationData);
            
            // 2. 显示确认对话框
            const userConfirmation = await this.dialog.show(confirmationInfo);
            
            // 3. 提交确认
            const confirmResult = await this.confirmOperation(
                confirmationInfo.confirmation_token,
                userConfirmation
            );
            
            if (confirmResult.status === 'waiting_admin_approval') {
                // 需要管理员批准，显示提示
                alert('操作已确认，正在等待管理员批准');
                return { status: 'pending_admin_approval' };
            } else if (confirmResult.status === 'confirmed') {
                // 确认完成，执行实际操作
                return await actualOperation();
            }
            
        } catch (error) {
            console.error('确认过程出错:', error);
            throw error;
        }
    }

    async getPendingConfirmations() {
        try {
            const response = await fetch(`${this.baseURL}/pending`, {
                credentials: 'include'
            });
            
            const result = await response.json();
            return result.confirmations || [];
        } catch (error) {
            console.error('获取待确认操作失败:', error);
            return [];
        }
    }

    async getAdminPendingConfirmations() {
        try {
            const response = await fetch(`${this.baseURL}/admin/pending`, {
                credentials: 'include'
            });
            
            const result = await response.json();
            return result.confirmations || [];
        } catch (error) {
            console.error('获取管理员待批准操作失败:', error);
            return [];
        }
    }
}

// 全局实例
const globalConfirmationManager = new ConfirmationManager();

// 便捷函数
window.confirmSensitiveOperation = async (operation, operationData, actualOperation) => {
    return await globalConfirmationManager.executeWithConfirmation(
        operation, 
        operationData, 
        actualOperation
    );
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ConfirmationDialog,
        ConfirmationManager,
        confirmationManager: globalConfirmationManager
    };
}

if (typeof window !== 'undefined') {
    window.ConfirmationDialog = ConfirmationDialog;
    window.ConfirmationManager = ConfirmationManager;
    window.confirmationManager = globalConfirmationManager;
}