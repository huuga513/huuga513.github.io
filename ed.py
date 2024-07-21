import os
import sys
import shutil
d = "e:/blogs"
os.chdir(d)
cwd = os.getcwd()
print("working at", cwd)

exec_cmd = lambda x:os.system(x)

def append_file(src, dst):
    """append the content of src to dst,
    both src and dst must exist
    """
    with open(src, 'rb') as srcf:
        content = srcf.read()
    with open(dst, 'ab') as dstf:
        dstf.write(content)

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print(f'usage: python {sys.argv[0]} <filename> [postname]')
        exit(1)
    filename = sys.argv[1]
    if (not os.path.exists(filename)):
        print(f'the file {filename} does not exist!')
        exit(1)
    
    postname = ''
    if (len(sys.argv) < 3):
        basename = os.path.splitext(os.path.basename(filename))[0]
        postname = basename
    else:
        postname = sys.argv[2]
    print(f'new blog will be post with name:{postname}')
    
    post_filename = postname+'.md'
    post_path = 'source/_posts/'+post_filename
    if (os.path.exists(post_path)):
        print(f"error: post {post_filename} has existed")
        exit(1)
    exec_cmd(f'hexo new {postname}')
    assert(os.path.exists(post_path))
    
    print(f"begin copying {filename} to {post_filename}...")
    append_file(filename, post_path)

    exec_cmd('hexo g')

    print("To preview the content, use 'hexo s'.\nTo deploy the content, use 'hexo d'")
    
    
    