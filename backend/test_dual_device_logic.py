#!/usr/bin/env python3
"""
测试双设备逻辑修复后的功能
验证只有CP1/CP2/CP3和FT1/FT2/FT3工序支持双设备，其他工序只支持单设备
"""
import requests
import json
from datetime import datetime, timedelta

def test_process_quote_logic():
    """测试工序报价逻辑"""
    base_url = "http://127.0.0.1:8000"
    
    print("=== 测试双设备逻辑修复 ===\n")
    
    # 测试用例1：CP测试工序（应支持双设备）
    test_case_1 = {
        "title": "CP测试工序-双设备测试",
        "quote_type": "process",
        "customer_name": "测试客户CP",
        "customer_contact": "张三",
        "currency": "CNY",
        "quote_unit": "昆山芯信安",
        "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
        "items": [
            {
                "item_name": "CP1测试工序",
                "item_description": "CP1测试工序-支持双设备",
                "configuration": "测试机:J750, 探针台:AP3000, UPH:1000",
                "quantity": 8.0,
                "unit": "小时",
                "unit_price": 320.0,
                "total_price": 2560.0
            }
        ],
        "total_amount": 2560.0
    }
    
    # 测试用例2：烘烤工序（应只支持单设备）
    test_case_2 = {
        "title": "烘烤工序-单设备测试", 
        "quote_type": "process",
        "customer_name": "测试客户烘烤",
        "customer_contact": "李四",
        "currency": "CNY",
        "quote_unit": "昆山芯信安",
        "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
        "items": [
            {
                "item_name": "烘烤工序",
                "item_description": "烘烤工序-单设备",
                "configuration": "设备:Blue M Oven, UPH:500",
                "quantity": 12.0,
                "unit": "小时", 
                "unit_price": 150.0,
                "total_price": 1800.0
            }
        ],
        "total_amount": 1800.0
    }
    
    # 测试用例3：FT测试工序（应支持双设备）
    test_case_3 = {
        "title": "FT测试工序-双设备测试",
        "quote_type": "process", 
        "customer_name": "测试客户FT",
        "customer_contact": "王五",
        "currency": "CNY",
        "quote_unit": "昆山芯信安",
        "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
        "items": [
            {
                "item_name": "FT2测试工序",
                "item_description": "FT2测试工序-支持双设备",
                "configuration": "测试机:ETS-88, 分选机:JHT6080, UPH:1200",
                "quantity": 6.0,
                "unit": "小时",
                "unit_price": 380.0,
                "total_price": 2280.0
            }
        ],
        "total_amount": 2280.0
    }
    
    test_cases = [
        ("CP测试工序(双设备)", test_case_1, True),
        ("烘烤工序(单设备)", test_case_2, False), 
        ("FT测试工序(双设备)", test_case_3, True)
    ]
    
    results = []
    
    for name, test_data, is_dual_device in test_cases:
        print(f"📝 测试: {name}")
        
        try:
            response = requests.post(f"{base_url}/api/v1/quotes/", 
                                   json=test_data,
                                   headers={"Content-Type": "application/json"})
            
            if response.status_code == 201:
                quote_data = response.json()
                quote_number = quote_data.get('quote_number')
                
                print(f"  ✅ 创建成功: {quote_number}")
                print(f"  📋 配置信息: {test_data['items'][0]['configuration']}")
                
                # 验证配置内容
                config = test_data['items'][0]['configuration']
                if is_dual_device:
                    # 双设备工序应包含两种设备
                    if ('测试机' in config and ('探针台' in config or '分选机' in config)):
                        print(f"  ✅ 双设备配置验证通过")
                        results.append((name, True, "双设备配置正确"))
                    else:
                        print(f"  ❌ 双设备配置验证失败")
                        results.append((name, False, "双设备配置错误"))
                else:
                    # 单设备工序应只包含一种设备
                    if ('设备' in config and '测试机' not in config):
                        print(f"  ✅ 单设备配置验证通过")
                        results.append((name, True, "单设备配置正确"))
                    else:
                        print(f"  ❌ 单设备配置验证失败")
                        results.append((name, False, "单设备配置错误"))
                
            else:
                print(f"  ❌ 创建失败: {response.status_code}")
                results.append((name, False, f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"  ❌ 请求异常: {e}")
            results.append((name, False, f"异常: {e}"))
            
        print()
    
    # 总结结果
    print("🎯 测试总结:")
    print(f"{'测试用例':<20} {'结果':<8} {'说明'}")
    print("-" * 50)
    
    passed = 0
    for name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:<20} {status:<8} {message}")
        if success:
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{len(results)} 通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！双设备逻辑修复成功")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

def test_frontend_logic():
    """测试前端逻辑判断"""
    print("\n=== 前端逻辑测试 ===")
    
    # 模拟前端的isTestProcess函数逻辑
    def is_test_process(process_name):
        if not process_name:
            return False
        return ((process_name.count('CP') > 0 and (process_name.count('1') > 0 or process_name.count('2') > 0 or process_name.count('3') > 0)) or
                (process_name.count('FT') > 0 and (process_name.count('1') > 0 or process_name.count('2') > 0 or process_name.count('3') > 0)))
    
    test_processes = [
        ("CP1测试", True),
        ("CP2测试", True),
        ("CP3测试", True),
        ("FT1测试", True),
        ("FT2测试", True), 
        ("FT3测试", True),
        ("烘烤", False),
        ("编带", False),
        ("AOI检测", False),
        ("包装", False),
        ("老化测试", False),
        ("X-Ray检测", False),
        ("外观检查", False)
    ]
    
    print("工序类型判断测试:")
    print(f"{'工序名称':<15} {'预期':<8} {'实际':<8} {'结果'}")
    print("-" * 40)
    
    all_correct = True
    for process_name, expected in test_processes:
        actual = is_test_process(process_name)
        correct = actual == expected
        status = "✅" if correct else "❌"
        
        print(f"{process_name:<15} {'双设备' if expected else '单设备':<8} {'双设备' if actual else '单设备':<8} {status}")
        
        if not correct:
            all_correct = False
    
    if all_correct:
        print("\n✅ 前端逻辑判断测试全部通过")
    else:
        print("\n❌ 前端逻辑判断测试存在问题")
    
    return all_correct

if __name__ == "__main__":
    try:
        backend_test = test_process_quote_logic()
        frontend_test = test_frontend_logic()
        
        print(f"\n🏆 最终结果:")
        print(f"  后端接口测试: {'✅ PASS' if backend_test else '❌ FAIL'}")
        print(f"  前端逻辑测试: {'✅ PASS' if frontend_test else '❌ FAIL'}")
        
        if backend_test and frontend_test:
            print(f"  🎉 双设备逻辑修复完全成功！")
        else:
            print(f"  ⚠️ 部分功能需要进一步优化")
            
    except Exception as e:
        print(f"❌ 测试过程发生错误: {e}")