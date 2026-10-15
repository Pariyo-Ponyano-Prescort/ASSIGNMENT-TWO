README.m
Project overview: Develops a Python-based tax calculator using the assignment's sample Ugandan tax rules.

Objective: Demonstrates Object-Oriented Programming (OOP), reusable code, validation, modular design and testing.

Main features: Calculates PAYE, payroll deductions, employee and employer NSSF contributions, VAT and corporate tax, and compares tax scenarios.

Core components: Money handles monetary values; Tax defines an abstract tax interface; PAYE calculates income tax; PayrollResult stores payroll results.

Project structure: tax_engine.py contains reusable tax calculations under src/, while project2_uganda_tax_engine.ipynb demonstrates calculations and results.

Technologies: Python, Decimal, dataclasses, abstract classes, type hints and pytest.

How to run: Install dependencies, import the tax engine into the notebook, and run all cells to test the calculations.

Testing and limitations: Tests should cover normal cases, boundary values and invalid inputs. The tax rates and rules are simplified assignment assumptions and should not be treated as verified current tax law.