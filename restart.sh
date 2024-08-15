# 清除进程并挂起

echo "Stopping all related processes..."
ps aux | grep "nb run --reload"
ps aux | grep "Lagrange.OneBot"

kill_process() {
    pids=$(pgrep -f $1)
    if [ ! -z "$pids" ]; then
        echo "Killing $1..."
        kill $pids
    else
        echo "No process found for $1"
    fi
}

echo "Stopping all related processes..."
kill_process "nb"
kill_process "OneBot"

sleep 1

echo "Starting ..."
cd LumiBot
nohup nb run --reload > nb.log 2>&1 &
cd ..
cd Lagrange.OneBot
nohup ./Lagrange.OneBot > Lagrange.log 2>&1 &

echo "Start OK!"
ps aux | grep nb
ps aux | grep OneBot
