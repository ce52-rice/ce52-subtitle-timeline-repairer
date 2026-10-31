from .checks import plain, report_problem, result, saved_problem


def verify_input(value):
    problem = report_problem(plain(value))
    return result(not problem, problem or "well formed selection")


def verify_output(input_value, output_value, workspace):
    given, report = plain(input_value), plain(output_value)
    problem = saved_problem(report, workspace)
    if given != report:
        problem = "save tool changed the submitted selection"
    return result(not problem, problem or "selection saved exactly")
