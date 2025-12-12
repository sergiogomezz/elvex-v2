import threading
import time
import sys
import itertools

def landing_intro():
    intro_message = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         🧠 Welcome to Elvex: Emergent Reasoning          ║
    ║               Through Autonomous Agents 🤖               ║
    ║                                                          ║
    ║   This system coordinates multiple LLM agents to help    ║
    ║   you explore, solve and simulate complex scenarios.     ║
    ║                                                          ║
    ║   Sit back, type your request, and let the agents think. ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(intro_message)


def loading_animation(message="🤖 Agents are working on your request... ✅"):
    '''
    Makes an imaginary loading tab
    '''
    stop_event = threading.Event()

    def animate():
        for c in itertools.cycle(['.', '..', '...', '....']):
            if stop_event.is_set():
                break
            sys.stdout.write(f'\r{message}{c}   ')
            sys.stdout.flush()
            time.sleep(0.5)

    time.sleep(2)

    t = threading.Thread(target=animate)
    t.start()
    return stop_event.set